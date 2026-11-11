package dev.dragonsteelschools.client;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.client.resources.model.ModelBakery;
import net.minecraft.client.resources.model.ModelResourceLocation;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ClientPlayerNetworkEvent;
import net.minecraftforge.client.event.ModelEvent;
import net.minecraftforge.client.event.RenderLivingEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * Client half of Elsewhere's moving blade (ElsewhereRenderer draws it).
 * <ul>
 *   <li>Bakes the six piece models (tip, middle, hilt, each with a full-bright _glow layer) and swaps Elsewhere's
 *   item model for {@link ElsewhereBakedModel}, which hands the in-hand views to the renderer.</li>
 *   <li>Remembers which living entity is being drawn, so a third-person view knows whose blade it is.</li>
 *   <li>Watches every wielder's swings and dodges (ElsewhereScatterPacket) and turns each into a spread that
 *   outlasts the arm: the blade flies apart in 2 ticks, stays apart while the arm comes back, then snaps together
 *   with a small overshoot. Tied to the 6-tick arm swing alone (dev.15) it was too quick to see in first person.</li>
 * </ul>
 * If a piece model fails to load, Elsewhere simply stays the flat sprite.
 */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID, value = Dist.CLIENT)
public final class ElsewhereClient {
    static final ModelResourceLocation ITEM_MODEL =
            new ModelResourceLocation(new ResourceLocation(DragonsteelSchools.MODID, "elsewhere"), "inventory");
    /** Index order the renderer relies on: tip, tip glow, middle, middle glow, hilt, hilt glow. */
    static final ResourceLocation[] PIECE_MODELS = new ResourceLocation[6];
    /** A swing's spread lasts 16 ticks (0.8 s), a dodge's scatter 22 (1.1 s). tools/elsewhere_motion.py mirrors both. */
    static final int SWING_TICKS = 16;
    static final int SCATTER_TICKS = 22;

    /** amount: -0.15..1 (negative is the overshoot as the pieces snap home); side: +1/-1, alternating swing to swing. */
    record Pulse(float amount, int side) {
        static final Pulse NONE = new Pulse(0F, 1);
    }

    private record Swing(long start, InteractionHand hand, int count) {
    }

    private record Seen(boolean swinging, int swingTime) {
    }

    private static volatile BakedModel[] pieces;
    private static final Deque<LivingEntity> RENDERING = new ArrayDeque<>();
    private static final Map<Integer, Seen> SEEN = new HashMap<>();
    private static final Map<Integer, Swing> SWINGS = new HashMap<>();
    private static final Map<Integer, Long> SCATTERS = new HashMap<>();

    static {
        String[] names = {"tip", "middle", "hilt"};
        for (int i = 0; i < names.length; i++) {
            PIECE_MODELS[2 * i] = new ResourceLocation(DragonsteelSchools.MODID, "item/elsewhere_" + names[i]);
            PIECE_MODELS[2 * i + 1] = new ResourceLocation(DragonsteelSchools.MODID, "item/elsewhere_" + names[i] + "_glow");
        }
    }

    private ElsewhereClient() {
    }

    /** The baked pieces, or null before baking (or if any failed to load). */
    static BakedModel[] pieces() {
        return pieces;
    }

    /** The living entity whose render is in progress, or null outside one (first person, GUI). */
    static LivingEntity renderingEntity() {
        return RENDERING.peek();
    }

    /** From ElsewhereScatterPacket: this entity's Elsewhere has just carried it out of a projectile's path. */
    public static void scatter(int entityId) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level != null) {
            SCATTERS.put(entityId, mc.level.getGameTime());
        }
    }

    /** The spread left by this holder's latest swing of the blade held in this hand. */
    static Pulse swing(LivingEntity holder, InteractionHand hand) {
        Swing swing = SWINGS.get(holder.getId());
        if (swing == null || swing.hand() != hand) {
            return Pulse.NONE;
        }
        return new Pulse(swingEnvelope(age(swing.start())), swing.count() % 2 == 1 ? 1 : -1);
    }

    /** 0..1, with a small negative overshoot at the end: how far a recent dodge has flung the blade apart. */
    static float scatter(LivingEntity holder) {
        Long start = SCATTERS.get(holder.getId());
        return start == null ? 0F : scatterEnvelope(age(start));
    }

    static float swingEnvelope(double a) {
        if (a < 0.0 || a >= SWING_TICKS) {
            return 0F;
        }
        if (a < 2.0) {
            return easeOut(a / 2.0);
        }
        if (a < 7.0) {
            return 1F;
        }
        if (a < 12.0) {
            return 1F - easeIn((a - 7.0) / 5.0);
        }
        return (float) (-0.15 * Math.sin(Math.PI * (a - 12.0) / 4.0));
    }

    static float scatterEnvelope(double a) {
        if (a < 0.0 || a >= SCATTER_TICKS) {
            return 0F;
        }
        if (a < 2.0) {
            return easeOut(a / 2.0);
        }
        if (a < 6.0) {
            return 1F;
        }
        if (a < 18.0) {
            return 1F - easeInOut((a - 6.0) / 12.0);
        }
        return (float) (-0.12 * Math.sin(Math.PI * (a - 18.0) / 4.0));
    }

    private static float easeOut(double x) {
        double k = 1.0 - x;
        return (float) (1.0 - k * k * k);
    }

    private static float easeIn(double x) {
        return (float) (x * x * x);
    }

    private static float easeInOut(double x) {
        return (float) (x < 0.5 ? 4.0 * x * x * x : 1.0 - Math.pow(-2.0 * x + 2.0, 3) / 2.0);
    }

    /** Ticks since a recorded game time, with this frame's partial tick. */
    private static double age(long start) {
        Minecraft mc = Minecraft.getInstance();
        return mc.level == null ? Double.MAX_VALUE : mc.level.getGameTime() - start + (double) mc.getPartialTick();
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onRenderLivingPre(RenderLivingEvent.Pre<?, ?> event) {
        RENDERING.push(event.getEntity());
    }

    @SubscribeEvent
    public static void onRenderLivingPost(RenderLivingEvent.Post<?, ?> event) {
        if (RENDERING.peek() == event.getEntity()) {
            RENDERING.pop();
        }
    }

    @SubscribeEvent
    public static void onRenderTick(TickEvent.RenderTickEvent event) {
        if (event.phase == TickEvent.Phase.START) {
            RENDERING.clear();   // a cancelled render never posts Post; never let one leak into the next frame
        }
    }

    /**
     * Spots each new swing of an Elsewhere: a wielder that has started swinging, or whose swing restarted (swingTime
     * went back), with the blade in the swinging hand. The same for the player, other players and mobs.
     */
    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            SEEN.clear();
            SWINGS.clear();
            SCATTERS.clear();
            return;
        }
        long now = mc.level.getGameTime();
        Item blade = ModItems.SWORD.get(SchoolSteel.ENDER).get();
        Set<Integer> wielders = new HashSet<>();
        for (Entity entity : mc.level.entitiesForRendering()) {
            if (!(entity instanceof LivingEntity living)
                    || !(living.getMainHandItem().is(blade) || living.getOffhandItem().is(blade))) {
                continue;
            }
            int id = living.getId();
            wielders.add(id);
            Seen before = SEEN.put(id, new Seen(living.swinging, living.swingTime));
            boolean fresh = living.swinging && (before == null || !before.swinging() || living.swingTime < before.swingTime());
            if (fresh && living.swingingArm != null && living.getItemInHand(living.swingingArm).is(blade)) {
                Swing last = SWINGS.get(id);
                SWINGS.put(id, new Swing(now, living.swingingArm, last == null ? 1 : last.count() + 1));
            }
        }
        SEEN.keySet().retainAll(wielders);
        SWINGS.values().removeIf(swing -> now - swing.start() > 4L * SWING_TICKS || swing.start() > now);
        SCATTERS.values().removeIf(start -> now - start > 2L * SCATTER_TICKS || start > now);
    }

    @SubscribeEvent
    public static void onLogout(ClientPlayerNetworkEvent.LoggingOut event) {
        SEEN.clear();
        SWINGS.clear();
        SCATTERS.clear();
        RENDERING.clear();
    }

    @Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Models {
        private Models() {
        }

        @SubscribeEvent
        public static void register(ModelEvent.RegisterAdditional event) {
            for (ResourceLocation model : PIECE_MODELS) {
                event.register(model);
            }
        }

        @SubscribeEvent
        public static void bake(ModelEvent.ModifyBakingResult event) {
            Map<ResourceLocation, BakedModel> models = event.getModels();
            BakedModel flat = models.get(ITEM_MODEL);
            BakedModel missing = models.get(ModelBakery.MISSING_MODEL_LOCATION);
            BakedModel[] found = new BakedModel[PIECE_MODELS.length];
            for (int i = 0; i < found.length; i++) {
                found[i] = models.get(PIECE_MODELS[i]);
                if (found[i] == null || found[i] == missing) {
                    DragonsteelSchools.LOG.warn("Elsewhere: piece model {} did not load; the blade stays flat in the hand", PIECE_MODELS[i]);
                    pieces = null;
                    return;
                }
            }
            if (flat == null || flat == missing) {
                pieces = null;
                return;
            }
            pieces = found;
            models.put(ITEM_MODEL, new ElsewhereBakedModel(flat));
        }
    }
}
