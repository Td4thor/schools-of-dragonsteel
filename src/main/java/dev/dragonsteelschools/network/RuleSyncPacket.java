package dev.dragonsteelschools.network;

import dev.dragonsteelschools.forge.FinishingRule;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraftforge.network.NetworkEvent;

import java.util.function.Supplier;

/** Tells a client which finishing rule the server enforces, so tempered steel's tooltip names the right spells. */
public record RuleSyncPacket(FinishingRule rule) {
    public static void encode(RuleSyncPacket packet, FriendlyByteBuf buf) {
        buf.writeEnum(packet.rule);
    }

    public static RuleSyncPacket decode(FriendlyByteBuf buf) {
        return new RuleSyncPacket(buf.readEnum(FinishingRule.class));
    }

    public static void handle(RuleSyncPacket packet, Supplier<NetworkEvent.Context> context) {
        // Only stores an enum in a common class, so it is safe on either side.
        FinishingRule.setSynced(packet.rule);
        context.get().setPacketHandled(true);
    }
}
