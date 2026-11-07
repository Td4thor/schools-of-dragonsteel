package dev.dragonsteelschools.combat;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.cauldron.SchoolCauldrons;
import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.item.SchoolSwordItem;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.EvokerFangs;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.entity.player.AttackEntityEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * The powers of the named school swords.
 * <ul>
 *   <li><b>Thirst</b> (Blood): heals the wielder for a share of the health its own hits remove, sweeps included.</li>
 *   <li><b>Covenant</b> (Evocation): a fully charged hit calls a row of evoker fangs toward the target.</li>
 *   <li><b>Briar</b> (Nature): hits poison and slow.</li>
 *   <li><b>Hush</b> (Eldritch): hits deal extra damage after armour, and players struck are wrapped in Darkness.</li>
 * </ul>
 * "Its own hits" means melee damage dealt directly by the wielder holding the sword in the main hand
 * (player or mob attack damage), never spells, projectiles or thorns.
 */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID)
public final class SwordPowers {
    /** Game time of each player's last fully charged swing, read when that swing lands. */
    private static final Map<UUID, Long> CHARGED_SWING = new ConcurrentHashMap<>();

    private SwordPowers() {
    }

    /** Called from {@link SchoolSwordItem#hurtEnemy} on the server after a hit lands on its main target. */
    public static void onHit(SchoolSteel school, LivingEntity target, LivingEntity attacker) {
        switch (school) {
            case EVOCATION -> {
                if (attacker instanceof Player player && chargedThisTick(player)) {
                    callFangs(player, target);
                }
            }
            case NATURE -> {
                int poison = DSConfig.seconds(DSConfig.BRIAR_POISON_SECONDS);
                int slow = DSConfig.seconds(DSConfig.BRIAR_SLOW_SECONDS);
                if (poison > 0) {
                    target.addEffect(new MobEffectInstance(MobEffects.POISON, poison, 0), attacker);
                }
                if (slow > 0) {
                    target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, slow, 1), attacker);
                }
            }
            case ELDRITCH -> {
                int darkness = DSConfig.seconds(DSConfig.HUSH_DARKNESS_SECONDS);
                if (darkness > 0 && target instanceof Player) {
                    target.addEffect(new MobEffectInstance(MobEffects.DARKNESS, darkness + 20, 0), attacker);
                }
            }
            default -> {
            }
        }
    }

    /** Numbers shown in each sword's power tooltip. */
    public static Object[] tooltipArgs(SchoolSteel school) {
        return switch (school) {
            case BLOOD -> new Object[]{fmt(DSConfig.get(DSConfig.THIRST_LIFESTEAL) * 100.0)};
            case EVOCATION -> new Object[]{DSConfig.get(DSConfig.COVENANT_FANGS), fmt(DSConfig.get(DSConfig.COVENANT_COOLDOWN_SECONDS))};
            case NATURE -> new Object[]{DSConfig.get(DSConfig.BRIAR_POISON_SECONDS), DSConfig.get(DSConfig.BRIAR_SLOW_SECONDS)};
            case ELDRITCH -> new Object[]{fmt(DSConfig.get(DSConfig.HUSH_BONUS_DAMAGE)), DSConfig.get(DSConfig.HUSH_DARKNESS_SECONDS)};
            default -> new Object[0];
        };
    }

    @SubscribeEvent
    public static void onAttack(AttackEntityEvent event) {
        Player player = event.getEntity();
        if (!player.level().isClientSide && player.getAttackStrengthScale(0.5F) >= 0.9F) {
            CHARGED_SWING.put(player.getUUID(), player.level().getGameTime());
        }
    }

    /** Hush: extra damage after armour, protection and absorption, so armour can't blunt it. */
    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void onDamageHush(LivingDamageEvent event) {
        if (ownHit(event.getSource(), SchoolSteel.ELDRITCH) != null) {
            event.setAmount(event.getAmount() + DSConfig.get(DSConfig.HUSH_BONUS_DAMAGE).floatValue());
        }
    }

    /** Thirst: runs last, on the health the hit will actually remove (overkill doesn't count). */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onDamageThirst(LivingDamageEvent event) {
        LivingEntity attacker = ownHit(event.getSource(), SchoolSteel.BLOOD);
        LivingEntity target = event.getEntity();
        if (attacker == null || attacker == target || !attacker.isAlive()) {
            return;
        }
        float removed = Math.min(event.getAmount(), target.getHealth());
        float heal = removed * DSConfig.get(DSConfig.THIRST_LIFESTEAL).floatValue();
        if (heal <= 0.0F) {
            return;
        }
        attacker.heal(heal);
        if (attacker.level() instanceof ServerLevel level) {
            Vec3 from = target.position().add(0, target.getBbHeight() * 0.6, 0);
            Vec3 to = attacker.position().add(0, attacker.getBbHeight() * 0.6, 0);
            for (int i = 0; i <= 6; i++) {
                Vec3 p = from.lerp(to, i / 6.0);
                level.sendParticles(SchoolCauldrons.dust(SchoolSteel.BLOOD, 0.9F), p.x, p.y, p.z, 2, 0.08, 0.08, 0.08, 0.0);
            }
        }
    }

    /** The attacker if this damage is a direct melee hit by someone holding the school's sword in the main hand. */
    private static LivingEntity ownHit(DamageSource source, SchoolSteel school) {
        if (!(source.getEntity() instanceof LivingEntity attacker) || source.getDirectEntity() != attacker) {
            return null;
        }
        if (!(source.is(DamageTypes.PLAYER_ATTACK) || source.is(DamageTypes.MOB_ATTACK)) || source.is(DamageTypeTags.IS_PROJECTILE)) {
            return null;
        }
        ItemStack held = attacker.getMainHandItem();
        return held.getItem() instanceof SchoolSwordItem sword && sword.school() == school ? attacker : null;
    }

    private static boolean chargedThisTick(Player player) {
        Long tick = CHARGED_SWING.remove(player.getUUID());
        return tick != null && tick == player.level().getGameTime();
    }

    private static void callFangs(Player player, LivingEntity target) {
        ItemStack held = player.getMainHandItem();
        if (player.getCooldowns().isOnCooldown(held.getItem())) {
            return;
        }
        int cooldown = DSConfig.ticks(DSConfig.COVENANT_COOLDOWN_SECONDS);
        if (cooldown > 0) {
            player.getCooldowns().addCooldown(held.getItem(), cooldown);
        }
        ServerLevel level = (ServerLevel) player.level();
        double minY = Math.min(target.getY(), player.getY()) - 1.0;
        double maxY = Math.max(target.getY(), player.getY()) + 1.0;
        float yaw = (float) Mth.atan2(target.getZ() - player.getZ(), target.getX() - player.getX());
        int fangs = DSConfig.get(DSConfig.COVENANT_FANGS);
        for (int i = 0; i < fangs; i++) {
            double d = 1.25 * (i + 1);
            spawnFang(level, player, player.getX() + Mth.cos(yaw) * d, player.getZ() + Mth.sin(yaw) * d, minY, maxY, yaw, 2 + 2 * i);
        }
        level.playSound(null, player.blockPosition(), SoundEvents.EVOKER_CAST_SPELL, SoundSource.PLAYERS, 0.8F, 1.2F);
    }

    /** Vanilla's evoker fang placement: the first standing spot between maxY and minY. */
    private static void spawnFang(ServerLevel level, Entity owner, double x, double z, double minY, double maxY, float yaw, int warmup) {
        BlockPos pos = BlockPos.containing(x, maxY, z);
        double offset = 0.0;
        boolean found = false;
        do {
            BlockPos below = pos.below();
            BlockState under = level.getBlockState(below);
            if (under.isFaceSturdy(level, below, Direction.UP)) {
                if (!level.isEmptyBlock(pos)) {
                    VoxelShape shape = level.getBlockState(pos).getCollisionShape(level, pos);
                    if (!shape.isEmpty()) {
                        offset = shape.max(Direction.Axis.Y);
                    }
                }
                found = true;
                break;
            }
            pos = pos.below();
        } while (pos.getY() >= Mth.floor(minY) - 1);
        if (found && owner instanceof LivingEntity living) {
            level.addFreshEntity(new EvokerFangs(level, x, pos.getY() + offset, z, yaw, warmup, living));
        }
    }

    private static String fmt(double value) {
        return value == Math.rint(value) ? Integer.toString((int) value) : String.format(java.util.Locale.ROOT, "%.1f", value);
    }
}
