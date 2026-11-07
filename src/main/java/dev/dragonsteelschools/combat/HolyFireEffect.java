package dev.dragonsteelschools.combat;

import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.registry.ModRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobType;
import net.minecraft.world.entity.player.Player;

import java.util.UUID;

/**
 * Holy fire: one hit of damage a second that ignores armour, like ordinary burning, and double against undead.
 * It is a status effect, not vanilla fire, so water and fire resistance do nothing to it; milk still cures it.
 * The damage source has no attacker (no knockback every second); kill credit is restored by hand instead.
 */
public class HolyFireEffect extends MobEffect {
    public HolyFireEffect() {
        super(MobEffectCategory.HARMFUL, 0xFFD36B);
    }

    @Override
    public boolean isDurationEffectTick(int duration, int amplifier) {
        return duration % 20 == 0;
    }

    @Override
    public void applyEffectTick(LivingEntity entity, int amplifier) {
        if (!(entity.level() instanceof ServerLevel level)) {
            return;
        }
        float damage = DSConfig.get(DSConfig.HOLY_FIRE_DAMAGE).floatValue();
        if (entity.getMobType() == MobType.UNDEAD) {
            damage *= DSConfig.get(DSConfig.HOLY_FIRE_UNDEAD_MULTIPLIER).floatValue();
        }
        UUID igniterId = HolyFire.igniter(entity);
        if (igniterId != null) {
            Entity igniter = level.getEntity(igniterId);
            if (igniter instanceof LivingEntity living && living != entity) {
                entity.setLastHurtByMob(living);
                if (living instanceof Player player) {
                    entity.setLastHurtByPlayer(player);
                }
            }
        }
        entity.hurt(ModRegistries.holyFire(level), damage);
    }
}
