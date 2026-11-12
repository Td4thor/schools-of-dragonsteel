package dev.dragonsteelschools.network;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkEvent;

import java.util.function.Supplier;

/**
 * Tells clients an entity's Elsewhere has just dodged from (x, y, z): its blade shatters in the hand and reassembles,
 * and the world shows it breaking where the wielder stood.
 */
public record ElsewhereScatterPacket(int entityId, double x, double y, double z) {
    public static void encode(ElsewhereScatterPacket packet, FriendlyByteBuf buf) {
        buf.writeVarInt(packet.entityId);
        buf.writeDouble(packet.x);
        buf.writeDouble(packet.y);
        buf.writeDouble(packet.z);
    }

    public static ElsewhereScatterPacket decode(FriendlyByteBuf buf) {
        return new ElsewhereScatterPacket(buf.readVarInt(), buf.readDouble(), buf.readDouble(), buf.readDouble());
    }

    public static void handle(ElsewhereScatterPacket packet, Supplier<NetworkEvent.Context> context) {
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT,
                () -> () -> dev.dragonsteelschools.client.ElsewhereClient.scatter(packet.entityId, packet.x, packet.y, packet.z));
        context.get().setPacketHandled(true);
    }
}
