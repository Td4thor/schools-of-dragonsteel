package dev.dragonsteelschools.combat;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.network.DSNetwork;
import dev.dragonsteelschools.network.ElsewhereScatterPacket;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.ForgeEventFactory;
import net.minecraftforge.event.entity.EntityTeleportEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.network.PacketDistributor;

/**
 * Elsewhere: while the blade is held, a projectile that would strike its wielder finds them gone. The step is an
 * enderman's (EnderMan.teleport in 1.20.1): random spot, drop to solid non-water ground, Forge's ender-teleport
 * event (so claim mods can veto), then vanilla randomTeleport's collision checks. Riders are never moved, so
 * nobody is thrown off a flying dragon.
 */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID)
public final class ElsewhereDodge {
    private static final int ATTEMPTS = 64;

    private ElsewhereDodge() {
    }

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void onAttack(LivingAttackEvent event) {
        LivingEntity target = event.getEntity();
        if (target.level().isClientSide || event.isCanceled() || target.isPassenger() || target.isSleeping()) {
            return;
        }
        Item blade = ModItems.SWORD.get(SchoolSteel.ENDER).get();
        boolean held = target.getMainHandItem().is(blade)
                || (DSConfig.get(DSConfig.ELSEWHERE_OFFHAND) && target.getOffhandItem().is(blade));
        if (!held || !isProjectile(event.getSource()) || event.getSource().getEntity() == target) {
            return;
        }
        if (target instanceof Player player && player.getCooldowns().isOnCooldown(blade)) {
            return;
        }
        if (step(target, DSConfig.get(DSConfig.ELSEWHERE_RADIUS), DSConfig.get(DSConfig.ELSEWHERE_VERTICAL))) {
            event.setCanceled(true);
            // the wielder and everyone watching see the blade fly apart and reassemble (ElsewhereRenderer)
            DSNetwork.CHANNEL.send(PacketDistributor.TRACKING_ENTITY_AND_SELF.with(() -> target), new ElsewhereScatterPacket(target.getId()));
            int cooldown = DSConfig.ticks(DSConfig.ELSEWHERE_COOLDOWN_SECONDS);
            if (cooldown > 0 && target instanceof Player player) {
                player.getCooldowns().addCooldown(blade, cooldown);
            }
        }
    }

    static boolean isProjectile(DamageSource source) {
        if (source.is(DamageTypeTags.IS_PROJECTILE)) {
            return true;
        }
        return DSConfig.get(DSConfig.ELSEWHERE_SPELL_PROJECTILES) && source.getDirectEntity() instanceof Projectile;
    }

    /** Up to 64 enderman-style attempts. */
    public static boolean step(LivingEntity entity, int radius, int vertical) {
        for (int i = 0; i < ATTEMPTS; i++) {
            double x = entity.getX() + (entity.getRandom().nextDouble() - 0.5) * 2.0 * radius;
            double y = entity.getY() + (entity.getRandom().nextInt(2 * vertical + 1) - vertical);
            double z = entity.getZ() + (entity.getRandom().nextDouble() - 0.5) * 2.0 * radius;
            if (tryStep(entity, x, y, z)) {
                return true;
            }
        }
        return false;
    }

    private static boolean tryStep(LivingEntity entity, double x, double y, double z) {
        Level level = entity.level();
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos(x, y, z);
        while (cursor.getY() > level.getMinBuildHeight() && !level.getBlockState(cursor).blocksMotion()) {
            cursor.move(Direction.DOWN);
        }
        BlockState ground = level.getBlockState(cursor);
        if (!ground.blocksMotion() || ground.getFluidState().is(FluidTags.WATER)) {
            return false;
        }
        EntityTeleportEvent.EnderEntity teleport = ForgeEventFactory.onEnderTeleport(entity, x, y, z);
        if (teleport.isCanceled()) {
            return false;
        }
        Vec3 from = entity.position();
        boolean moved = entity.randomTeleport(teleport.getTargetX(), teleport.getTargetY(), teleport.getTargetZ(), true);
        if (moved) {
            level.gameEvent(GameEvent.TELEPORT, from, GameEvent.Context.of(entity));
            level.playSound(null, from.x, from.y, from.z, SoundEvents.ENDERMAN_TELEPORT, entity.getSoundSource(), 1.0F, 1.0F);
            level.playSound(null, entity.getX(), entity.getY(), entity.getZ(), SoundEvents.ENDERMAN_TELEPORT, entity.getSoundSource(), 1.0F, 1.0F);
        }
        return moved;
    }
}
