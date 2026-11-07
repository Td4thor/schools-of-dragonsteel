package dev.dragonsteelschools.network;

import dev.dragonsteelschools.DragonsteelSchools;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;

public final class DSNetwork {
    private static final String VERSION = "1";
    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            new ResourceLocation(DragonsteelSchools.MODID, "main"), () -> VERSION, VERSION::equals, VERSION::equals);

    private DSNetwork() {
    }

    public static void register() {
        CHANNEL.messageBuilder(HolyFireSyncPacket.class, 0, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(HolyFireSyncPacket::encode)
                .decoder(HolyFireSyncPacket::decode)
                .consumerMainThread(HolyFireSyncPacket::handle)
                .add();
    }
}
