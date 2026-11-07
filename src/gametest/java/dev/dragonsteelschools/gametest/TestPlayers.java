package dev.dragonsteelschools.gametest;

import com.mojang.authlib.GameProfile;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelOutboundHandlerAdapter;
import io.netty.channel.ChannelPromise;
import io.netty.channel.embedded.EmbeddedChannel;
import io.netty.util.AttributeKey;
import io.netty.util.ReferenceCountUtil;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.ConnectionProtocol;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.GameType;
import net.minecraftforge.network.NetworkConstants;

import java.util.UUID;

/**
 * Real survival players logged in through {@code PlayerList.placeNewPlayer} over an in-memory Netty channel,
 * so Forge login hooks and Iron's capabilities attach as they do for a client. Not a real client.
 * (The built-in GameTest mock player reports itself as creative, which Iron's treats as cost- and cooldown-free.)
 */
final class TestPlayers {
    private TestPlayers() {
    }

    static ServerPlayer create(GameTestHelper helper) {
        Connection connection = new Connection(PacketFlow.SERVERBOUND);
        EmbeddedChannel channel = new EmbeddedChannel();
        channel.pipeline().addLast("test_outbound_sink", new ChannelOutboundHandlerAdapter() {
            @Override
            public void write(ChannelHandlerContext context, Object message, ChannelPromise promise) {
                ReferenceCountUtil.release(message);
                promise.setSuccess();
            }
        });
        channel.pipeline().addLast("packet_handler", connection);
        try {
            connection.channelActive(channel.pipeline().context(connection));
            connection.setProtocol(ConnectionProtocol.PLAY);
            // An in-memory channel skips the handshake that normally sets this Forge marker.
            channel.attr(AttributeKey.<String>valueOf("fml:netversion")).set(NetworkConstants.NETVERSION);
            ServerPlayer player = new ServerPlayer(helper.getLevel().getServer(), helper.getLevel(),
                    new GameProfile(UUID.randomUUID(), "ds" + UUID.randomUUID().toString().substring(0, 10)));
            helper.getLevel().getServer().getPlayerList().placeNewPlayer(connection, player);
            player.setGameMode(GameType.SURVIVAL);
            player.setNoGravity(true);
            return player;
        } catch (Exception failure) {
            channel.finishAndReleaseAll();
            throw new IllegalStateException("Native test player login failed", failure);
        }
    }

    static void remove(ServerPlayer player) {
        if (!player.hasDisconnected()) {
            player.server.getPlayerList().remove(player);
        }
    }
}
