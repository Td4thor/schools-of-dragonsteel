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
 * a pulsing beam of light strung across each cut and a glint running along it.
 * <ul>
 *   <li>At rest the tip and the middle length hover a little apart, drift, rock and tilt.</li>
 *   <li>On each swing they fly apart (the tip out toward the blade's back and up, the middle out the other way,
 *   both twisting, the twist alternating swing to swing), hold while the arm comes back, then snap together with a
 *   small overshoot (ElsewhereClient.swingEnvelope).</li>
 *   <li>When the dodge fires (ElsewhereScatterPacket) the shards scatter wide and spin, then reassemble.</li>
 * </ul>
 * The hilt never moves: the hand holds it. Cut faces, the Eye and the beams are drawn full-bright.
 *
 * <p>Distances are in sprite pixels (the 32 px sprite spans one model block) and angles in degrees. The pose
 * arrives with the flat sprite's display transform applied, so every piece sits exactly where its pixels sit on the
 * sprite when all offsets are zero. Pieces never move toward the blade's edge in the sprite plane (-across, +slip):
 * in first person that carries them at the camera until they fill the view. tools/elsewhere_motion.py mirrors these
 * numbers for software previews and checks how close any piece comes to the camera.
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
        float t = mc.level == null ? 0F : (float) (mc.level.getGameTime() % 240_000L) + mc.getPartialTick();
        LivingEntity holder = context.firstPerson() ? mc.player : ElsewhereClient.renderingEntity();
        ElsewhereClient.Pulse swing = holder == null ? ElsewhereClient.Pulse.NONE : ElsewhereClient.swing(holder, hand(holder, context));
        float sw = swing.amount();
        float s = sw * swing.side();
        float sc = holder == null ? 0F : ElsewhereClient.scatter(holder);

        Placement tip = Placement.of(25.0F, 5.5F,
                1.0F + 0.6F * Mth.sin(t * 0.07F) + 2.0F * sw + 3.0F * sc,                  // along, toward the point
                0.8F * Mth.sin(t * 0.043F + 1.3F) + 5.0F * sw + 7.0F * sc,                 // across, toward the back
                0F,                                                                         // slip, sideways
                0.8F * Mth.sin(t * 0.055F) + 3.0F * sw + 5.0F * sc,                        // out of the sprite plane
                3.5F * Mth.sin(t * 0.05F + 0.4F) + 25.0F * s + 140.0F * sc,                // roll in the plane
                6.0F * Mth.sin(t * 0.037F + 2.0F) + 20.0F * s + 50.0F * sc);               // tilt out of it
        Placement middle = Placement.of(20.0F, 12.5F,
                0.5F + 0.4F * Mth.sin(t * 0.07F + 1.2F) + 1.5F * sw + 3.0F * sc,
                0F,
                1.0F * Mth.sin(t * 0.031F + 0.6F),
                -0.6F * Mth.sin(t * 0.055F + 0.9F) - 3.0F * sw - 5.0F * sc,
                -2.5F * Mth.sin(t * 0.045F + 1.7F) - 14.0F * s - 100.0F * sc,
                -4.5F * Mth.sin(t * 0.041F) - 10.0F * s - 30.0F * sc);

        ItemRenderer items = mc.getItemRenderer();
        piece(items, stack, pose, buffers, pieces[4], pieces[5], STILL, light, overlay);
        piece(items, stack, pose, buffers, pieces[2], pieces[3], middle, light, overlay);
        piece(items, stack, pose, buffers, pieces[0], pieces[1], tip, light, overlay);

        float energy = Math.max(Math.abs(sw), sc);
        Light glow = new Light(
                Mth.clamp((int) (205 + 40 * Mth.sin(t * 0.21F) + 40 * energy), 0, 255),
                Mth.clamp((int) (70 + 25 * Mth.sin(t * 0.13F + 1.0F) + 110 * Math.abs(sw) + 150 * sc), 0, 235),
                (3.0F + 0.6F * Mth.sin(t * 0.17F) + 1.5F * energy) * PX);
        float run = t * 0.05F;
        VertexConsumer beams = buffers.getBuffer(RenderType.entityTranslucentEmissive(THREAD));
        beam(beams, pose, tip.point(23.5F, 8.0F), middle.point(23.5F, 10.0F), glow, run - Mth.floor(run));             // upper cut
        beam(beams, pose, middle.point(17.5F, 15.0F), STILL.point(14.5F, 17.0F), glow, run + 0.5F - Mth.floor(run + 0.5F)); // lower cut
    }

    /** Which of the holder's hands this view draws. */
    private static InteractionHand hand(LivingEntity holder, ItemDisplayContext context) {
        boolean right = context == ItemDisplayContext.FIRST_PERSON_RIGHT_HAND || context == ItemDisplayContext.THIRD_PERSON_RIGHT_HAND;
        HumanoidArm arm = right ? HumanoidArm.RIGHT : HumanoidArm.LEFT;
        return holder.getMainArm() == arm ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND;
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

    /** Beam brightness: core alpha, halo alpha, halo width (model units). */
    private record Light(int core, int halo, float haloWidth) {
    }

    /**
     * A beam from a to b: a soft violet halo, a bright core and a glint at fraction {@code glint} of the way along,
     * each as two crossed strips so it shows edge-on.
     */
    private static void beam(VertexConsumer out, PoseStack pose, Vector3f a, Vector3f b, Light light, float glint) {
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
        Vector3f span = new Vector3f(to).sub(from);
        float half = Math.min(0.08F, 1.2F * PX / Math.max(span.length(), PX));
        Vector3f g0 = new Vector3f(span).mul(Math.max(0F, glint - half)).add(from);
        Vector3f g1 = new Vector3f(span).mul(Math.min(1F, glint + half)).add(from);
        int glintAlpha = (int) (255 * Mth.sin(glint * Mth.PI));
        Matrix4f m = pose.last().pose();
        Matrix3f n = pose.last().normal();
        for (Vector3f across : new Vector3f[]{side, depth}) {
            strip(out, m, n, from, to, across, light.haloWidth(), 168, 95, 255, light.halo());
            strip(out, m, n, from, to, across, 1.0F * PX, 245, 230, 255, light.core());
            strip(out, m, n, g0, g1, across, 1.8F * PX, 255, 255, 255, glintAlpha);
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
         * cx, cy: the piece's centre on the sprite (pixels, y down). along: toward the point; across: toward the
         * blade's back; slip: sideways (sprite +x); out: depth. roll turns it in the sprite plane, tilt out of it.
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
