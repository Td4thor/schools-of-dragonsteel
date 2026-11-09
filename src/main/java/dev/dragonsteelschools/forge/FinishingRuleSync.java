package dev.dragonsteelschools.forge;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.network.DSNetwork;
import dev.dragonsteelschools.network.RuleSyncPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.server.ServerLifecycleHooks;

/** Sends the server's {@link FinishingRule} to each player on login, and to everyone when the config reloads. */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID)
public final class FinishingRuleSync {
    private FinishingRuleSync() {
    }

    @SubscribeEvent
    public static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer player) {
            DSNetwork.CHANNEL.send(PacketDistributor.PLAYER.with(() -> player), new RuleSyncPacket(FinishingRule.active()));
        }
    }

    /** Called after a config load or reload; does nothing until a server is running. */
    public static void broadcast() {
        MinecraftServer server = ServerLifecycleHooks.getCurrentServer();
        if (server != null && server.isRunning()) {
            server.execute(() -> DSNetwork.CHANNEL.send(PacketDistributor.ALL.noArg(), new RuleSyncPacket(FinishingRule.active())));
        }
    }
}
