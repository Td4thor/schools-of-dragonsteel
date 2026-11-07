package dev.dragonsteelschools.combat;

import dev.dragonsteelschools.registry.ModRegistries;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import org.jetbrains.annotations.Nullable;

import java.util.UUID;

/** Lights holy fire on a target and remembers who lit it, so kills by the burn credit the wielder. */
public final class HolyFire {
    static final String IGNITER_KEY = "dragonsteel_schools.holy_fire_by";

    private HolyFire() {
    }

    public static void ignite(LivingEntity target, @Nullable Entity igniter, int ticks) {
        // No vanilla effect particles: the burn draws its own flames and embers on the client.
        target.addEffect(new MobEffectInstance(ModRegistries.HOLY_FIRE.get(), ticks, 0, false, false, true), igniter);
        if (igniter != null) {
            target.getPersistentData().putUUID(IGNITER_KEY, igniter.getUUID());
        }
    }

    public static boolean isBurning(LivingEntity entity) {
        return entity.hasEffect(ModRegistries.HOLY_FIRE.get());
    }

    @Nullable
    static UUID igniter(LivingEntity target) {
        return target.getPersistentData().hasUUID(IGNITER_KEY) ? target.getPersistentData().getUUID(IGNITER_KEY) : null;
    }
}
