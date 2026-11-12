package dev.dragonsteelschools.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.dragonsteelschools.DragonsteelSchools;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.block.model.BakedQuad;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
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
 * Elsewhere in the hand. The blade is ten shards in three lengths (ElsewhereShards), drawn as extruded sprites
 * like any held item, with pulsing beams of light across the two cuts.
 * <ul>
 *   <li><b>At rest</b> the tip and the middle length hover apart and drift on layered slow waves. Every five
 *   seconds or so one of them blinks a little way elsewhere and drifts home.</li>
 *   <li><b>On a swing</b> they fly apart (the tip out toward the blade's back and up, the middle out the other way,
 *   both twisting, the twist alternating swing to swing), hold while the arm comes back, ease home and settle
 *   with a damped wobble. Quick swings carry on from where the last one left the pieces.</li>
 *   <li><b>On a dodge</b> the whole blade shatters: every shard flies outward on its own line, spinning, drifts,
 *   is drawn home in turn along a thread of light from the Eye, spiralling in, and clicks into place with a small
 *   rock. In first person the shards burst into a ring round the blade on screen (every direction, all of it in
 *   view); in third person they fly out round the blade in the world.</li>
 *   <li>Anything moving fast leaves violet afterimages: the same motion drawn 0.9, 1.8 and 2.7 ticks ago, fainter
 *   the slower it moves.</li>
 * </ul>
 * The hilt never moves: the hand holds it. Cut faces, the Eye, beams and afterimages are drawn full-bright.
 *
 * <p>Distances are in sprite pixels (the 32 px sprite spans one model block) and angles in degrees. The pose
 * arrives with the flat sprite's display transform applied, so every piece sits exactly where its pixels sit on the
 * sprite when all offsets are zero. In first person a shard is never allowed nearer the eye than CAMERA_MARGIN (a
 * piece pushed toward the blade's edge in the sprite plane heads straight at the camera). tools/elsewhere_motion.py
 * mirrors all of this for software previews.
 */
final class ElsewhereRenderer extends BlockEntityWithoutLevelRenderer {
    private static final float PX = 1.0F / 32.0F;
    private static final float R2 = (float) Math.sqrt(0.5);
    private static final float DEG = Mth.DEG_TO_RAD;
    private static final int N = ElsewhereShards.NAMES.length;
    private static final float CAMERA_MARGIN = 0.26F;
    /** The hand's fixed 70 degree projection: 1 / tan(35 degrees). */
    private static final float FOCAL = 1.4281F;
    /**
     * First-person shatter, in normalised screen units (the screen spans -1..1 each way): how far a shard flies at
     * 12 px of flight (half again toward the open screen on the left), how far the whole cloud drifts toward the
     * middle, and how near the edge a shard's centre may go.
     */
    private static final float SCREEN_REACH = 0.42F;
    private static final float SCREEN_WIDE = 0.9F;
    private static final float SCREEN_DRIFT = 0.25F;
    private static final float SCREEN_EDGE = 0.95F;
    private static final float GHOST_STEP = 0.9F;
    private static final float[] GHOST_ALPHA = {0.36F, 0.22F, 0.13F};
    private static final float[] EYE = {9.5F, 21.5F};
    private static final ResourceLocation THREAD = new ResourceLocation(DragonsteelSchools.MODID, "textures/misc/elsewhere_thread.png");
    private static final Direction[] FACES = Direction.values();
    private static final RandomSource RANDOM = RandomSource.create();

    ElsewhereRenderer() {
        super(Minecraft.getInstance().getBlockEntityRenderDispatcher(), Minecraft.getInstance().getEntityModels());
    }

    @Override
    public void renderByItem(ItemStack stack, ItemDisplayContext context, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        ElsewhereClient.Models models = ElsewhereClient.models();
        if (models == null) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        float t = mc.level == null ? 0F : (float) (mc.level.getGameTime() % 240_000L) + mc.getPartialTick();
        LivingEntity holder = context.firstPerson() ? mc.player : ElsewhereClient.renderingEntity();
        ElsewhereClient.State state = holder == null ? ElsewhereClient.State.NONE : ElsewhereClient.state(holder, hand(holder, context));
        Matrix4f view = context.firstPerson() ? new Matrix4f(pose.last().pose()) : null;
        float aspect = (float) mc.getWindow().getWidth() / Math.max(1, mc.getWindow().getHeight());
        Frame now = Frame.at(t, state, 0F, view, aspect);

        ItemRenderer items = mc.getItemRenderer();
        draw(items, stack, pose, buffers, models.hilt(), light, overlay);
        draw(items, stack, pose, buffers, models.hiltGlow(), LightTexture.FULL_BRIGHT, overlay);
        for (int i = 0; i < N; i++) {
            push(pose, now.shard[i]);
            draw(items, stack, pose, buffers, models.shard()[i], light, overlay);
            if (models.shardGlow()[i] != null) {
                draw(items, stack, pose, buffers, models.shardGlow()[i], LightTexture.FULL_BRIGHT, overlay);
            }
            pose.popPose();
        }

        VertexConsumer ghosts = null;
        for (int k = 0; k < GHOST_ALPHA.length; k++) {
            Frame then = Frame.at(t, state, GHOST_STEP * (k + 1), view, aspect);
            for (int i = 0; i < N; i++) {
                float alpha = GHOST_ALPHA[k] * speed(now.shard[i], then.shard[i], i);
                if (alpha < 0.01F) {
                    continue;
                }
                if (ghosts == null) {
                    ghosts = buffers.getBuffer(RenderType.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS));
                }
                push(pose, then.shard[i]);
                ghost(ghosts, pose, models.shard()[i], alpha);
                if (models.shardGlow()[i] != null) {
                    ghost(ghosts, pose, models.shardGlow()[i], alpha);
                }
                pose.popPose();
            }
        }

        VertexConsumer light2 = buffers.getBuffer(RenderType.entityTranslucentEmissive(THREAD));
        Matrix4f m = pose.last().pose();
        Matrix3f n = pose.last().normal();
        float beamsLeft = 1F - Mth.clamp(now.maxFlight * 5F, 0F, 1F);
        if (beamsLeft > 0F) {
            int halo = Mth.clamp((int) ((70 + 25 * Mth.sin(t * 0.13F + 1.0F) + 110 * now.swing) * beamsLeft), 0, 235);
            int core = Mth.clamp((int) ((205 + 40 * Mth.sin(t * 0.21F) + 40 * now.swing) * beamsLeft), 0, 255);
            float width = (3.0F + 0.6F * Mth.sin(t * 0.17F) + 1.5F * now.swing) * PX;
            float run = t * 0.05F;
            beam(light2, m, n, point(now.shard[ElsewhereShards.UPPER_TIP], 23.5F, 8.0F),
                    point(now.shard[ElsewhereShards.UPPER_MIDDLE], 23.5F, 10.0F), core, halo, width, run - Mth.floor(run), beamsLeft);
            beam(light2, m, n, point(now.shard[ElsewhereShards.LOWER_MIDDLE], 17.5F, 15.0F),
                    point(now.shard[ElsewhereShards.LOWER_BASE], 14.5F, 17.0F), core, halo, width, run + 0.5F - Mth.floor(run + 0.5F), beamsLeft);
        }
        Vector3f eye = new Vector3f(EYE[0] * PX, 1F - EYE[1] * PX, 0.5F);
        for (int i = 0; i < N; i++) {
            float stagger = ElsewhereShards.FLIGHT[i][8];
            float alpha = ElsewhereClient.tether(state.scatterAge(), stagger)
                    * Math.min(1F, 2F * ElsewhereClient.flight(state.scatterAge(), stagger));   // fades as it shortens
            if (alpha > 0.01F) {
                tether(light2, m, n, eye, point(now.shard[i], ElsewhereShards.CENTRE[i][0], ElsewhereShards.CENTRE[i][1]), alpha, i, t);
            }
        }
    }

    /** Where every shard is at time t - back. */
    private static final class Frame {
        final Matrix4f[] shard = new Matrix4f[N];
        float maxFlight;
        float swing;

        static Frame at(float t, ElsewhereClient.State state, float back, Matrix4f view, float aspect) {
            Frame f = new Frame();
            float tt = t - back;
            float swTip = state.spread(ElsewhereClient.TIP, back);
            float swMid = state.spread(ElsewhereClient.MIDDLE, back);
            float side = state.side();
            f.swing = Math.max(Math.abs(swTip), Math.abs(swMid));
            float[] blink = blink(tt);
            float bTip = blink[0] == 0F ? blink[1] : 0F;
            float bMid = blink[0] == 1F ? blink[1] : 0F;

            Matrix4f tip = segment(25.0F, 5.5F,
                    1.0F + 0.45F * Mth.sin(tt * 0.07F) + 0.2F * Mth.sin(tt * 0.173F + 2.1F) + 2.0F * swTip,
                    0.6F * Mth.sin(tt * 0.043F + 1.3F) + 0.25F * Mth.sin(tt * 0.131F) + 5.0F * swTip + 1.6F * bTip,
                    0F,
                    0.6F * Mth.sin(tt * 0.055F) + 0.25F * Mth.sin(tt * 0.149F + 0.7F) + 3.0F * swTip + 1.3F * blink[2] * bTip,
                    3.0F * Mth.sin(tt * 0.05F + 0.4F) + 1.2F * Mth.sin(tt * 0.161F + 1.9F) + 25.0F * side * swTip + 7.0F * blink[3] * bTip,
                    5.0F * Mth.sin(tt * 0.037F + 2.0F) + 2.0F * Mth.sin(tt * 0.113F) + 20.0F * side * swTip);
            Matrix4f middle = segment(20.0F, 12.5F,
                    0.5F + 0.3F * Mth.sin(tt * 0.07F + 1.2F) + 0.15F * Mth.sin(tt * 0.19F) + 1.5F * swMid,
                    1.6F * bMid,
                    0.8F * Mth.sin(tt * 0.031F + 0.6F),
                    -0.5F * Mth.sin(tt * 0.055F + 0.9F) - 0.2F * Mth.sin(tt * 0.137F + 2.4F) - 3.0F * swMid + 1.3F * blink[2] * bMid,
                    -2.2F * Mth.sin(tt * 0.045F + 1.7F) - 0.9F * Mth.sin(tt * 0.157F) - 14.0F * side * swMid + 7.0F * blink[3] * bMid,
                    -4.0F * Mth.sin(tt * 0.041F) - 1.5F * Mth.sin(tt * 0.121F + 1.1F) - 10.0F * side * swMid);
            Matrix4f[] segments = {tip, middle, new Matrix4f()};

            double scatterAge = state.scatterAge() - back;
            for (int i = 0; i < N; i++) {
                Matrix4f seg = segments[ElsewhereShards.SEGMENT[i]];
                float[] fl = ElsewhereShards.FLIGHT[i];
                float p = ElsewhereClient.flight(scatterAge, fl[8]);
                float rock = ElsewhereClient.wobble(scatterAge, fl[8]);
                f.maxFlight = Math.max(f.maxFlight, p);
                if (p == 0F && rock == 0F) {
                    f.shard[i] = seg;
                    continue;
                }
                Vector3f home = seg.transformPosition(new Vector3f(ElsewhereShards.CENTRE[i][0] * PX, 1F - ElsewhereShards.CENTRE[i][1] * PX, 0.5F));
                float swirl = 80F * DEG * ElsewhereClient.recall(scatterAge, fl[8]) * (i % 2 == 0 ? 1F : -1F);
                Vector3f d = view == null ? worldFlight(fl, p, swirl) : screenFlight(view, home, fl, p, swirl, aspect);
                float turn = p <= 1F ? p : 1F + 4F * (p - 1F);   // keeps turning through the drift
                Quaternionf spin = new Quaternionf().rotateAxis((fl[7] * turn + rock) * DEG, fl[4], fl[5], fl[6]);
                f.shard[i] = new Matrix4f().translation(home.x + d.x, home.y + d.y, home.z + d.z).rotate(spin)
                        .translate(-home.x, -home.y, -home.z).mul(seg);
            }
            return f;
        }
    }

    /** Third person: out along the shard's own line round the blade, the way back curling about the blade's face. */
    private static Vector3f worldFlight(float[] fl, float p, float swirl) {
        Vector3f d = new Vector3f(fl[0], fl[1], fl[2]).mul(fl[3] * PX * p);
        return swirl == 0F ? d : d.rotateZ(swirl);
    }

    /**
     * First person: out across the screen at the shard's own angle (a ring round the blade, every direction),
     * a little toward or away from the eye, never off the screen's edge or nearer the eye than CAMERA_MARGIN; the
     * way back curls about the line of sight. Worked in view space, returned in the model's.
     */
    private static Vector3f screenFlight(Matrix4f view, Vector3f home, float[] fl, float p, float swirl, float aspect) {
        Vector3f eyeHome = view.transformPosition(new Vector3f(home));
        float depth = Math.max(0.05F, -eyeHome.z);
        float hx = FOCAL / aspect * eyeHome.x / depth;
        float hy = FOCAL * eyeHome.y / depth;
        float angle = fl[9] * DEG + swirl;
        float reach = SCREEN_REACH * fl[3] / 12F * p * (1F + 0.5F * Math.max(0F, -Mth.cos(angle)));
        float sx = hx + Mth.cos(angle) * reach * SCREEN_WIDE - SCREEN_DRIFT * p;
        float sy = hy + Mth.sin(angle) * reach;
        float hold = Math.min(1F, p);   // the limits come in with the flight, so nothing jumps as it starts
        sx += (Mth.clamp(sx, -SCREEN_EDGE, SCREEN_EDGE) - sx) * hold;
        sy += (Mth.clamp(sy, -SCREEN_EDGE, SCREEN_EDGE) - sy) * hold;
        float z = Math.max(CAMERA_MARGIN, depth * (1F - 0.25F * fl[2] * p));
        Vector3f target = new Vector3f(sx * z * aspect / FOCAL, sy * z / FOCAL, -z);
        Vector3f model = new Matrix4f(view).invert().transformPosition(target);
        return model.sub(home);
    }

    /**
     * Every ~5 s one length blinks a little way elsewhere and drifts home over 14 ticks: {length (0 tip, 1 middle,
     * -1 none), amount, out sign, roll sign}.
     */
    static float[] blink(float tt) {
        int k = Mth.floor(tt / 100F);
        float u = (tt - (100F * k + 15F + 55F * hash(k))) / 14F;
        if (u < 0F || u >= 1F) {
            return new float[]{-1F, 0F, 0F, 0F};
        }
        return new float[]{hash(k + 0.37) < 0.5F ? 0F : 1F, 1F - ElsewhereClient.easeInOut(u),
                hash(k + 0.71) < 0.5F ? 1F : -1F, hash(k + 0.53) < 0.5F ? 1F : -1F};
    }

    static float hash(double x) {
        double v = Math.sin(x * 12.9898) * 43758.5453;
        return (float) (v - Math.floor(v));
    }

    /** A length of the blade turned about its centre (cx, cy: sprite pixels) and moved; see the class notes. */
    private static Matrix4f segment(float cx, float cy, float along, float across, float slip, float out, float roll, float tilt) {
        float px = cx * PX;
        float py = 1.0F - cy * PX;
        float dx = ((along - across) * R2 + slip) * PX;
        float dy = (along + across) * R2 * PX;
        Quaternionf q = new Quaternionf().rotateZ(roll * DEG).rotateAxis(tilt * DEG, -R2, R2, 0F);
        return new Matrix4f().translation(px + dx, py + dy, 0.5F + out * PX).rotate(q).translate(-px, -py, -0.5F);
    }

    /** A sprite point (pixels, y down) carried by a shard's transform. */
    private static Vector3f point(Matrix4f shard, float sx, float sy) {
        return shard.transformPosition(new Vector3f(sx * PX, 1.0F - sy * PX, 0.5F));
    }

    /** 0..1: how strongly a shard that has moved this far since the earlier frame leaves an afterimage. */
    private static float speed(Matrix4f now, Matrix4f then, int i) {
        float cx = ElsewhereShards.CENTRE[i][0];
        float cy = ElsewhereShards.CENTRE[i][1];
        float moved = Math.max(point(now, cx, cy).distance(point(then, cx, cy)),
                point(now, cx + 2.5F, cy).distance(point(then, cx + 2.5F, cy))) / PX;
        return Mth.clamp((moved - 0.8F) / 2.5F, 0F, 1F);
    }

    private static void push(PoseStack pose, Matrix4f m) {
        pose.pushPose();
        pose.last().pose().mul(m);
        pose.last().normal().mul(new Matrix3f(m));   // rigid: its upper 3x3 is a rotation
    }

    /** Which of the holder's hands this view draws. */
    private static InteractionHand hand(LivingEntity holder, ItemDisplayContext context) {
        boolean right = context == ItemDisplayContext.FIRST_PERSON_RIGHT_HAND || context == ItemDisplayContext.THIRD_PERSON_RIGHT_HAND;
        HumanoidArm arm = right ? HumanoidArm.RIGHT : HumanoidArm.LEFT;
        return holder.getMainArm() == arm ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND;
    }

    /** As ItemRenderer.render draws a non-block item's quads (glint included). */
    private static void draw(ItemRenderer items, ItemStack stack, PoseStack pose, MultiBufferSource buffers,
                             BakedModel model, int light, int overlay) {
        for (RenderType type : model.getRenderTypes(stack, true)) {
            items.renderModelLists(model, stack, light, overlay, pose, ItemRenderer.getFoilBufferDirect(buffers, type, true, stack.hasFoil()));
        }
    }

    /** A model's quads tinted violet, translucent and full-bright: an afterimage. */
    private static void ghost(VertexConsumer out, PoseStack pose, BakedModel model, float alpha) {
        for (Direction face : FACES) {
            RANDOM.setSeed(42L);
            for (BakedQuad quad : model.getQuads(null, face, RANDOM)) {
                out.putBulkData(pose.last(), quad, 0.80F, 0.58F, 1.0F, alpha, LightTexture.FULL_BRIGHT, OverlayTexture.NO_OVERLAY, false);
            }
        }
        RANDOM.setSeed(42L);
        for (BakedQuad quad : model.getQuads(null, null, RANDOM)) {
            out.putBulkData(pose.last(), quad, 0.80F, 0.58F, 1.0F, alpha, LightTexture.FULL_BRIGHT, OverlayTexture.NO_OVERLAY, false);
        }
    }

    /** A beam across a cut: a soft violet halo, a bright core and a glint running along it. */
    private static void beam(VertexConsumer out, Matrix4f m, Matrix3f n, Vector3f a, Vector3f b, int core, int halo,
                             float haloWidth, float glint, float fade) {
        Vector3f dir = new Vector3f(b).sub(a);
        if (dir.lengthSquared() < 1.0E-10F) {
            return;
        }
        dir.normalize();
        Vector3f from = new Vector3f(a).sub(new Vector3f(dir).mul(0.5F * PX));   // tuck the ends into the faces
        Vector3f to = new Vector3f(b).add(new Vector3f(dir).mul(0.5F * PX));
        line(out, m, n, from, to, haloWidth, 168, 95, 255, halo);
        line(out, m, n, from, to, 1.0F * PX, 245, 230, 255, core);
        Vector3f span = new Vector3f(to).sub(from);
        float half = Math.min(0.08F, 1.2F * PX / Math.max(span.length(), PX));
        Vector3f g0 = new Vector3f(span).mul(Math.max(0F, glint - half)).add(from);
        Vector3f g1 = new Vector3f(span).mul(Math.min(1F, glint + half)).add(from);
        line(out, m, n, g0, g1, 1.8F * PX, 255, 255, 255, (int) (255 * fade * Mth.sin(glint * Mth.PI)));
    }

    /** The flickering thread from the Eye to a flying shard, bent a little at three points. */
    private static void tether(VertexConsumer out, Matrix4f m, Matrix3f n, Vector3f eye, Vector3f end, float alpha, int i, float t) {
        Vector3f span = new Vector3f(end).sub(eye);
        float length = span.length();
        if (length < 1.0E-4F) {
            return;
        }
        Vector3f side = new Vector3f(span).cross(0F, 0F, 1F);
        if (side.lengthSquared() < 1.0E-8F) {
            side.set(1F, 0F, 0F);
        }
        side.normalize();
        int flicker = Mth.floor(t / 2F);
        Vector3f last = new Vector3f(eye);
        for (int j = 1; j <= 4; j++) {
            float f = j / 4F;
            Vector3f next = new Vector3f(span).mul(f).add(eye);
            if (j < 4) {
                next.add(new Vector3f(side).mul((hash(i * 7.0 + j + flicker * 13.0) - 0.5F) * 0.3F * length * Mth.sin(f * Mth.PI)));
            }
            line(out, m, n, last, next, 2.2F * PX, 168, 95, 255, (int) (110 * alpha));
            line(out, m, n, last, next, 0.7F * PX, 240, 220, 255, (int) (255 * alpha));
            last = next;
        }
    }

    /** A strip from a to b, drawn twice at right angles so it shows from any side. */
    private static void line(VertexConsumer out, Matrix4f m, Matrix3f n, Vector3f a, Vector3f b, float width, int r, int g, int bl, int alpha) {
        if (alpha <= 0) {
            return;
        }
        Vector3f dir = new Vector3f(b).sub(a);
        if (dir.lengthSquared() < 1.0E-12F) {
            return;
        }
        dir.normalize();
        Vector3f side = new Vector3f(dir).cross(0F, 0F, 1F);
        if (side.lengthSquared() < 1.0E-6F) {
            side.set(1F, 0F, 0F);
        }
        side.normalize();
        Vector3f depth = new Vector3f(dir).cross(side).normalize();
        strip(out, m, n, a, b, side, width, r, g, bl, alpha);
        strip(out, m, n, a, b, depth, width, r, g, bl, alpha);
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
        out.vertex(m, x, y, z).color(r, g, b, Math.min(255, alpha)).uv(u, v).overlayCoords(OverlayTexture.NO_OVERLAY)
                .uv2(LightTexture.FULL_BRIGHT).normal(n, 0F, 0F, 1F).endVertex();
    }
}
