package dev.dragonsteelschools.forge;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;

/** The block a caster is looking at, worked out on the server. */
public final class CastAim {
    private CastAim() {
    }

    public static Optional<BlockHitResult> blockInSight(ServerPlayer player, double range) {
        Vec3 eye = player.getEyePosition();
        // From the player's own rotation: the server's yHeadRot can lag behind a client (or a test fixture).
        Vec3 direction = Vec3.directionFromRotation(player.getXRot(), player.getYRot());
        Vec3 end = eye.add(direction.scale(range));
        BlockHitResult hit = player.level().clip(new ClipContext(eye, end, ClipContext.Block.OUTLINE, ClipContext.Fluid.NONE, player));
        return hit.getType() == HitResult.Type.BLOCK ? Optional.of(hit) : Optional.empty();
    }
}
