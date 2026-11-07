package dev.dragonsteelschools.combat;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.network.DSNetwork;
import dev.dragonsteelschools.network.HolyFireSyncPacket;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.registry.ModRegistries;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobType;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.event.entity.living.MobEffectEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.network.PacketDistributor;

/** Dawn's edge against the undead, and keeping every client's view of holy fire in step with the server. */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID)
public final class DawnEvents {
    private DawnEvents() {
    }

    @SubscribeEvent
    public static void onHurt(LivingHurtEvent event) {
        DamageSource source = event.getSource();
        if (!(source.getEntity() instanceof LivingEntity attacker) || source.getDirectEntity() != attacker) {
            return;
        }
        if (!attacker.getMainHandItem().is(ModItems.SWORD.get(SchoolSteel.HOLY).get())) {
            return;
        }
        if (event.getEntity().getMobType() == MobType.UNDEAD) {
            event.setAmount(event.getAmount() + DSConfig.get(DSConfig.DAWN_UNDEAD_BONUS).floatValue());
        }
    }

    @SubscribeEvent
    public static void onEffectAdded(MobEffectEvent.Added event) {
        MobEffectInstance instance = event.getEffectInstance();
        if (instance.getEffect() == ModRegistries.HOLY_FIRE.get() && !event.getEntity().level().isClientSide) {
            sync(event.getEntity(), instance.getDuration());
        }
    }

    @SubscribeEvent
    public static void onEffectRemoved(MobEffectEvent.Remove event) {
        if (event.getEffect() == ModRegistries.HOLY_FIRE.get() && !event.getEntity().level().isClientSide) {
            sync(event.getEntity(), 0);
        }
    }

    @SubscribeEvent
    public static void onEffectExpired(MobEffectEvent.Expired event) {
        MobEffectInstance instance = event.getEffectInstance();
        if (instance != null && instance.getEffect() == ModRegistries.HOLY_FIRE.get() && !event.getEntity().level().isClientSide) {
            sync(event.getEntity(), 0);
        }
    }

    @SubscribeEvent
    public static void onStartTracking(PlayerEvent.StartTracking event) {
        if (event.getTarget() instanceof LivingEntity target && event.getEntity() instanceof ServerPlayer player) {
            MobEffectInstance instance = target.getEffect(ModRegistries.HOLY_FIRE.get());
            if (instance != null) {
                DSNetwork.CHANNEL.send(PacketDistributor.PLAYER.with(() -> player),
                        new HolyFireSyncPacket(target.getId(), instance.getDuration()));
            }
        }
    }

    @SubscribeEvent
    public static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            MobEffectInstance instance = player.getEffect(ModRegistries.HOLY_FIRE.get());
            if (instance != null) {
                sync(player, instance.getDuration());
            }
        }
    }

    private static void sync(LivingEntity entity, int ticks) {
        DSNetwork.CHANNEL.send(PacketDistributor.TRACKING_ENTITY_AND_SELF.with(() -> entity), new HolyFireSyncPacket(entity.getId(), ticks));
    }
}
