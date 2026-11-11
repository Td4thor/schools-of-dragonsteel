package dev.dragonsteelschools.client;

import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/** Elsewhere's client extension: the renderer for its moving blade, made on first use (after the client is up). */
public final class ElsewhereClientExtensions implements IClientItemExtensions {
    private ElsewhereRenderer renderer;

    @Override
    public BlockEntityWithoutLevelRenderer getCustomRenderer() {
        if (renderer == null) {
            renderer = new ElsewhereRenderer();
        }
        return renderer;
    }
}
