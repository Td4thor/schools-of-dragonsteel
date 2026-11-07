package dev.dragonsteelschools.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import dev.dragonsteelschools.DragonsteelSchools;
import it.unimi.dsi.fastutil.ints.Int2LongMap;
import it.unimi.dsi.fastutil.ints.Int2LongOpenHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.Sheets;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.inventory.InventoryMenu;
import org.joml.Vector3f;

/**
 * What holy fire looks like: gold-white flames drawn over the burning entity the way vanilla draws fire (but with
 * our own animated sprites), rising embers and motes, and gold flames at the bottom of the screen for the burning
 * player in first person. Driven by {@code HolyFireSyncPacket}, since status effects of other entities are not
 * sent to clients.
 */
public final class HolyFireClient {
    private static final ResourceLocation FLAME_0 = new ResourceLocation(DragonsteelSchools.MODID, "block/holy_fire_0");
    private static final ResourceLocation FLAME_1 = new ResourceLocation(DragonsteelSchools.MODID, "block/holy_fire_1");
    private static final Int2LongMap BURNING_UNTIL = new Int2LongOpenHashMap();
    private static final Vector3f GOLD = new Vector3f(1.0F, 0.84F, 0.38F);
    private static final Vector3f WHITE_GOLD = new Vector3f(1.0F, 0.96F, 0.78F);

    private HolyFireClient() {
    }

    public static void update(int entityId, int ticks) {
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null) {
            return;
        }
        if (ticks <= 0) {
            BURNING_UNTIL.remove(entityId);
        } else {
            BURNING_UNTIL.put(entityId, level.getGameTime() + ticks);
        }
    }

    public static boolean isBurning(Entity entity) {
        long until = BURNING_UNTIL.getOrDefault(entity.getId(), Long.MIN_VALUE);
        return until != Long.MIN_VALUE && entity.level().getGameTime() <= until && entity.isAlive();
    }

    public static void clear() {
        BURNING_UNTIL.clear();
    }

    /** Per client tick: embers, and forgetting entities whose burn has ended or who have gone. */
    public static void tick() {
        Minecraft mc = Minecraft.getInstance();
        ClientLevel level = mc.level;
        if (level == null || BURNING_UNTIL.isEmpty() || mc.isPaused()) {
            return;
        }
        long now = level.getGameTime();
        RandomSource random = level.random;
        var it = BURNING_UNTIL.int2LongEntrySet().iterator();
        while (it.hasNext()) {
            Int2LongMap.Entry entry = it.next();
            Entity entity = level.getEntity(entry.getIntKey());
            if (entity == null || now > entry.getLongValue() || !entity.isAlive()) {
                it.remove();
                continue;
            }
            if (entity == mc.player && mc.options.getCameraType().isFirstPerson()) {
                continue;
            }
            double width = entity.getBbWidth();
            double height = entity.getBbHeight();
            for (int i = 0; i < 2; i++) {
                double x = entity.getX() + (random.nextDouble() - 0.5) * width * 1.3;
                double y = entity.getY() + random.nextDouble() * height;
                double z = entity.getZ() + (random.nextDouble() - 0.5) * width * 1.3;
                level.addParticle(new DustParticleOptions(random.nextBoolean() ? GOLD : WHITE_GOLD, 0.9F), x, y, z, 0.0, 0.05, 0.0);
            }
            if (random.nextInt(4) == 0) {
                level.addParticle(ParticleTypes.END_ROD, entity.getX() + (random.nextDouble() - 0.5) * width,
                        entity.getY() + height * (0.4 + random.nextDouble() * 0.6), entity.getZ() + (random.nextDouble() - 0.5) * width,
                        0.0, 0.04, 0.0);
            }
        }
    }

    /** Vanilla's EntityRenderDispatcher.renderFlame, with the holy fire sprites. The pose is at the entity's feet. */
    public static void renderFlames(PoseStack pose, MultiBufferSource buffers, Entity entity) {
        Minecraft mc = Minecraft.getInstance();
        var atlas = mc.getTextureAtlas(InventoryMenu.BLOCK_ATLAS);
        TextureAtlasSprite sprite0 = atlas.apply(FLAME_0);
        TextureAtlasSprite sprite1 = atlas.apply(FLAME_1);
        pose.pushPose();
        float scale = entity.getBbWidth() * 1.4F;
        pose.scale(scale, scale, scale);
        float halfWidth = 0.5F;
        float remaining = entity.getBbHeight() / scale;
        float yOffset = 0.0F;
        pose.mulPose(Axis.YP.rotationDegrees(-mc.gameRenderer.getMainCamera().getYRot()));
        pose.translate(0.0F, 0.0F, -0.3F + (float) ((int) remaining) * 0.02F);
        float depth = 0.0F;
        int layer = 0;
        VertexConsumer consumer = buffers.getBuffer(Sheets.cutoutBlockSheet());
        PoseStack.Pose last = pose.last();
        while (remaining > 0.0F) {
            TextureAtlasSprite sprite = layer % 2 == 0 ? sprite0 : sprite1;
            float u0 = sprite.getU0();
            float v0 = sprite.getV0();
            float u1 = sprite.getU1();
            float v1 = sprite.getV1();
            if (layer / 2 % 2 == 0) {
                float swap = u1;
                u1 = u0;
                u0 = swap;
            }
            vertex(last, consumer, halfWidth, -yOffset, depth, u1, v1);
            vertex(last, consumer, -halfWidth, -yOffset, depth, u0, v1);
            vertex(last, consumer, -halfWidth, 1.4F - yOffset, depth, u0, v0);
            vertex(last, consumer, halfWidth, 1.4F - yOffset, depth, u1, v0);
            remaining -= 0.45F;
            yOffset -= 0.45F;
            halfWidth *= 0.9F;
            depth += 0.03F;
            layer++;
        }
        pose.popPose();
    }

    private static void vertex(PoseStack.Pose pose, VertexConsumer consumer, float x, float y, float z, float u, float v) {
        consumer.vertex(pose.pose(), x, y, z).color(255, 255, 255, 255).uv(u, v)
                .overlayCoords(OverlayTexture.NO_OVERLAY).uv2(240).normal(pose.normal(), 0.0F, 1.0F, 0.0F).endVertex();
    }

    /** First person: two banks of gold flame rising from the bottom corners of the screen, like vanilla fire's. */
    public static void renderOverlay(GuiGraphics graphics) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || !mc.options.getCameraType().isFirstPerson() || !isBurning(mc.player)) {
            return;
        }
        TextureAtlasSprite sprite = mc.getTextureAtlas(InventoryMenu.BLOCK_ATLAS).apply(FLAME_1);
        int width = graphics.guiWidth();
        int height = graphics.guiHeight();
        int size = Math.max(width, height) / 3;
        RenderSystem.enableBlend();
        RenderSystem.setShaderColor(1.0F, 1.0F, 1.0F, 0.85F);
        graphics.blit(-size / 6, height - size + size / 5, 0, size, size, sprite);
        graphics.blit(width - size + size / 6, height - size + size / 5, 0, size, size, sprite);
        RenderSystem.setShaderColor(1.0F, 1.0F, 1.0F, 1.0F);
        RenderSystem.disableBlend();
    }
}
