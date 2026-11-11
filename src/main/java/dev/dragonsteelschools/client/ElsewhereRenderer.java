package dev.dragonsteelschools.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.dragonsteelschools.DragonsteelSchools;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * Elsewhere in the hand: the blade's three lengths drawn apart, each an extruded sprite like any held item, with
 * a beam of light strung across each cut.
 * <ul>
 *   <li>At rest the tip and the middle length hover a little apart and drift slowly.</li>
 *   <li>On a swing they fly apart along the blade (the tip about a quarter-block) and close again as the swing ends.</li>
 *   <li>When the dodge fires (ElsewhereScatterPacket) the shards scatter wide and reassemble within a second.</li>
 * </ul>
 * The hilt never moves: the hand holds it. Cut faces, the Eye and the beams are drawn full-bright.
 *
 * <p>Distances are in sprite pixels (the 32 px sprite spans one model block) and angles in degrees. The pose
 * arrives with the flat sprite's display transform applied, so every piece sits exactly where its pixels sit on the
 * sprite when all offsets are zero.
 */
final class ElsewhereRenderer extends BlockEntityWithoutLevelRenderer {
    private static final float PX = 1.0F / 32.0F;
    private static final float R2 = (float) Math.sqrt(0.5);
    private static final float DEG = Mth.DEG_TO_RAD;
    private static final ResourceLocation THREAD = new ResourceLocation(DragonsteelSchools.MODID, "textures/misc/elsewhere_thread.png");
    private static final Placement STILL = new Placement(0F, 0F, 0F, 0F, 0F, 0F, new Quaternionf());

    ElsewhereRenderer() {
        super(Minecraft.getInstance().getBlockEntityRenderDispatcher(), Minecraft.getInstance().getEntityModels());
    }

    @Override
    public void renderByItem(ItemStack stack, ItemDisplayContext context, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        BakedModel[] pieces = ElsewhereClient.pieces();
        if (pieces == null) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        float partial = mc.getPartialTick();
        float t = mc.level == null ? 0F : (float) (mc.level.getGameTime() % 240_000L) + partial;
        LivingEntity holder = context.firstPerson() ? mc.player : ElsewhereClient.renderingEntity();
        float swing = swing(holder, context, partial);
        float scatter = holder == null ? 0F : ElsewhereClient.scatter(holder);

        Placement tip = Placement.of(25.0F, 5.5F,
                1.5F + 0.75F * Mth.sin(t * 0.080F) + 8.0F * swing + 14.0F * scatter,           // along the blade
                0.6F * Mth.sin(t * 0.047F + 1.3F) + 2.5F * swing + 7.0F * scatter,             // across, to its back
                0F,
                0.5F * Mth.sin(t * 0.061F) + 2.0F * swing + 5.0F * scatter,                   // out of the sprite plane
                2.5F * Mth.sin(t * 0.053F + 0.4F) + 10.0F * swing + 50.0F * scatter,          // roll in the plane
                4.0F * Mth.sin(t * 0.039F + 2.0F) + 8.0F * swing + 25.0F * scatter);          // tilt out of it
        Placement middle = Placement.of(20.0F, 12.5F,
                0.75F + 0.5F * Mth.sin(t * 0.080F + 1.2F) + 4.0F * swing + 7.0F * scatter,
                0F,
                0.9F * Mth.sin(t * 0.035F + 0.6F) + 2.5F * swing - 6.0F * scatter,            // further out of line
                -0.4F * Mth.sin(t * 0.061F + 0.9F) - 2.0F * swing - 4.0F * scatter,
                -1.8F * Mth.sin(t * 0.047F + 1.7F) - 7.0F * swing - 40.0F * scatter,
                -3.0F * Mth.sin(t * 0.043F) - 6.0F * swing - 20.0F * scatter);

        ItemRenderer items = mc.getItemRenderer();
        piece(items, stack, pose, buffers, pieces[4], pieces[5], STILL, light, overlay);
        piece(items, stack, pose, buffers, pieces[2], pieces[3], middle, light, overlay);
        piece(items, stack, pose, buffers, pieces[0], pieces[1], tip, light, overlay);

        int halo = Mth.clamp((int) (80 + 70 * swing + 150 * scatter), 0, 230);
        VertexConsumer beams = buffers.getBuffer(RenderType.entityTranslucentEmissive(THREAD));
        beam(beams, pose, tip.point(23.5F, 8.0F), middle.point(23.5F, 10.0F), halo);       // the upper cut
        beam(beams, pose, middle.point(17.5F, 15.0F), STILL.point(14.5F, 17.0F), halo);   // the lower cut
    }

    /** 0..1 over the swing of the arm holding this blade: out to the peak and back. */
    private static float swing(LivingEntity holder, ItemDisplayContext context, float partial) {
        if (holder == null || holder.swingingArm == null) {
            return 0F;
        }
        boolean right = context == ItemDisplayContext.FIRST_PERSON_RIGHT_HAND || context == ItemDisplayContext.THIRD_PERSON_RIGHT_HAND;
        HumanoidArm arm = right ? HumanoidArm.RIGHT : HumanoidArm.LEFT;
        InteractionHand hand = holder.getMainArm() == arm ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND;
        if (holder.swingingArm != hand) {
            return 0F;
        }
        float progress = holder.getAttackAnim(partial);
        return progress <= 0F ? 0F : Mth.sin(progress * Mth.PI);
    }

    private static void piece(ItemRenderer items, ItemStack stack, PoseStack pose, MultiBufferSource buffers,
                              BakedModel body, BakedModel glow, Placement at, int light, int overlay) {
        pose.pushPose();
        at.apply(pose);
        draw(items, stack, pose, buffers, body, light, overlay);
        draw(items, stack, pose, buffers, glow, LightTexture.FULL_BRIGHT, overlay);
        pose.popPose();
    }

    /** As ItemRenderer.render draws a non-block item's quads (glint included). */
    private static void draw(ItemRenderer items, ItemStack stack, PoseStack pose, MultiBufferSource buffers,
                             BakedModel model, int light, int overlay) {
        for (RenderType type : model.getRenderTypes(stack, true)) {
            items.renderModelLists(model, stack, light, overlay, pose, ItemRenderer.getFoilBufferDirect(buffers, type, true, stack.hasFoil()));
        }
    }

    /** A beam from a to b: a bright core and a soft violet halo, each as two crossed strips so it shows edge-on. */
    private static void beam(VertexConsumer out, PoseStack pose, Vector3f a, Vector3f b, int halo) {
        Vector3f dir = new Vector3f(b).sub(a);
        float length = dir.length();
        if (length < 1.0E-5F) {
            return;
        }
        dir.div(length);
        Vector3f from = new Vector3f(a).sub(new Vector3f(dir).mul(0.5F * PX));   // tuck the ends into the faces
        Vector3f to = new Vector3f(b).add(new Vector3f(dir).mul(0.5F * PX));
        Vector3f side = new Vector3f(dir).cross(0F, 0F, 1F);
        if (side.lengthSquared() < 1.0E-6F) {
            side.set(1F, 0F, 0F);
        }
        side.normalize();
        Vector3f depth = new Vector3f(dir).cross(side).normalize();
        Matrix4f m = pose.last().pose();
        Matrix3f n = pose.last().normal();
        for (Vector3f across : new Vector3f[]{side, depth}) {
            strip(out, m, n, from, to, across, 3.0F * PX, 168, 95, 255, halo);
            strip(out, m, n, from, to, across, 1.0F * PX, 245, 230, 255, 240);
        }
    }

    private static void strip(VertexConsumer out, Matrix4f m, Matrix3f n, Vector3f a, Vector3f b, Vector3f across,
                              float width, int r, int g, int bl, int alpha) {
        float hx = across.x * width * 0.5F;
        float hy = across.y * width * 0.5F;
        float hz = across.z * width * 0.5F;
        vertex(out, m, n, a.x - hx, a.y - hy, a.z - hz, 0F, 0F, r, g, bl, alpha);
        vertex(out, m, n, a.x + hx, a.y + hy, a.z + hz, 1F, 0F, r, g, bl, alpha);
        vertex(out, m, n, b.x + hx, b.y + hy, b.z + hz, 1F, 1F, r, g, bl, alpha);
        vertex(out, m, n, b.x - hx, b.y - hy, b.z - hz, 0F, 1F, r, g, bl, alpha);
    }

    private static void vertex(VertexConsumer out, Matrix4f m, Matrix3f n, float x, float y, float z, float u, float v,
                               int r, int g, int b, int alpha) {
        out.vertex(m, x, y, z).color(r, g, b, alpha).uv(u, v).overlayCoords(OverlayTexture.NO_OVERLAY)
                .uv2(LightTexture.FULL_BRIGHT).normal(n, 0F, 0F, 1F).endVertex();
    }

    /**
     * Where a piece is drawn: turned about its own centre (the pivot, in model units) and moved by an offset.
     * The same transform places the beams' ends on its cut faces.
     */
    private record Placement(float px, float py, float pz, float ox, float oy, float oz, Quaternionf rot) {
        /**
         * @param cx, cy  the piece's centre on the sprite (pixels, y down)
         * @param along   toward the point; across: toward the blade's back; slip: sideways (sprite +x); out: depth
         */
        static Placement of(float cx, float cy, float along, float across, float slip, float out, float roll, float tilt) {
            float dx = ((along - across) * R2 + slip) * PX;
            float dy = (along + across) * R2 * PX;
            Quaternionf rot = new Quaternionf().rotateZ(roll * DEG).rotateAxis(tilt * DEG, -R2, R2, 0F);
            return new Placement(cx * PX, 1.0F - cy * PX, 0.5F, dx, dy, out * PX, rot);
        }

        void apply(PoseStack pose) {
            pose.translate(px + ox, py + oy, pz + oz);
            pose.mulPose(rot);
            pose.translate(-px, -py, -pz);
        }

        /** A point on the unmoved sprite (pixels, y down), where this placement carries it. */
        Vector3f point(float sx, float sy) {
            Vector3f v = new Vector3f(sx * PX - px, 1.0F - sy * PX - py, 0.5F - pz);
            rot.transform(v);
            return v.add(px + ox, py + oy, pz + oz);
        }
    }
}
