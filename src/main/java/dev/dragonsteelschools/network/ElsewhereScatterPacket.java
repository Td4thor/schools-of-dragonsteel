package dev.dragonsteelschools.network;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;

import java.util.function.Supplier;

/** Tells clients an entity's Elsewhere has just dodged, so its blade flies apart and reassembles in their view. */
public record ElsewhereScatterPacket(int entityId) {
    public static void encode(ElsewhereScatterPacket packet, FriendlyByteBuf buf) {
        buf.writeVarInt(packet.entityId);
    }

    public static ElsewhereScatterPacket decode(FriendlyByteBuf buf) {
        return new ElsewhereScatterPacket(buf.readVarInt());
    }

    public static void handle(ElsewhereScatterPacket packet, Supplier<NetworkEvent.Context> context) {
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT,
                () -> () -> dev.dragonsteelschools.client.ElsewhereClient.scatter(packet.entityId));
        context.get().setPacketHandled(true);
    }
}
