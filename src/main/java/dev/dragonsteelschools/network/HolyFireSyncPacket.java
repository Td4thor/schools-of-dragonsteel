package dev.dragonsteelschools.network;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;

import java.util.function.Supplier;

/** Tells clients an entity is burning with holy fire for {@code ticks} more ticks (0 = put out). */
public record HolyFireSyncPacket(int entityId, int ticks) {
    public static void encode(HolyFireSyncPacket packet, FriendlyByteBuf buf) {
        buf.writeVarInt(packet.entityId);
        buf.writeVarInt(packet.ticks);
    }

    public static HolyFireSyncPacket decode(FriendlyByteBuf buf) {
        return new HolyFireSyncPacket(buf.readVarInt(), buf.readVarInt());
    }

    public static void handle(HolyFireSyncPacket packet, Supplier<NetworkEvent.Context> context) {
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT,
                () -> () -> dev.dragonsteelschools.client.HolyFireClient.update(packet.entityId, packet.ticks));
        context.get().setPacketHandled(true);
    }
}
