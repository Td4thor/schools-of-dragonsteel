package dev.dragonsteelschools.client;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.client.resources.model.ModelBakery;
import net.minecraft.client.resources.model.ModelResourceLocation;
import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ClientPlayerNetworkEvent;
import net.minecraftforge.client.event.ModelEvent;
import net.minecraftforge.client.event.RenderLivingEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Client half of Elsewhere's moving blade (ElsewhereRenderer draws it).
 * <ul>
 *   <li>Bakes the blade's shard models (ElsewhereShards, cut by tools/generate_textures.py) and the hilt, and swaps
 *   Elsewhere's item model for {@link ElsewhereBakedModel}, which hands the in-hand views to the renderer.</li>
 *   <li>Remembers which living entity is being drawn, so a third-person view knows whose blade it is.</li>
 *   <li>Watches every wielder's swings. Each gives a spread that outlasts the arm: out in 2 ticks (from wherever the
 *   last swing left it, so quick swings never pop), held while the arm comes back, eased home, then a damped
 *   settle. The tip follows the middle by 0.7 ticks.</li>
 *   <li>On a dodge (ElsewhereScatterPacket) the blade shatters: the renderer flings every shard outward; here the
 *   world gets a burst of the blade's own fragments and violet light where the wielder stood, portal motes where
 *   they land, a glassy break and, as the shards click home, a chime.</li>
 * </ul>
 * If any model fails to load, Elsewhere simply stays the flat sprite.
 */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID, value = Dist.CLIENT)
public final class ElsewhereClient {
    static final ModelResourceLocation ITEM_MODEL =
            new ModelResourceLocation(new ResourceLocation(DragonsteelSchools.MODID, "elsewhere"), "inventory");
    static final int TIP = 0;
    static final int MIDDLE = 1;
    /** A swing's spread lasts 17 ticks; a shatter 28 (to the last shard's settle). tools/elsewhere_motion.py mirrors both. */
    static final int SWING_TICKS = 17;
    static final int SCATTER_TICKS = 28;
    /** Shatter timing (ticks): burst, hang (then each shard waits its stagger), the way home. */
    static final double BURST = 3.0;
    static final double HANG = 8.0;
    static final double RETURN = 6.0;
    /** Ticks into a shatter when the point, the last shard, is home and the chime sounds. */
    private static final double CHIME_AT = HANG + 8.0 + RETURN;

    /** Everything ElsewhereRenderer draws. shardGlow entries are null where a shard has no glowing pixels. */
    record Models(BakedModel hilt, BakedModel hiltGlow, BakedModel[] shard, BakedModel[] shardGlow) {
    }

    /** One wielder's motion at render time: ticks since the latest swing and shatter, and where the swing began. */
    record State(double swingAge, float s0Tip, float s0Middle, int side, double scatterAge) {
        static final State NONE = new State(Double.MAX_VALUE, 0F, 0F, 1, Double.MAX_VALUE);

        /** The swing spread of one length of the blade, {@code back} ticks ago. */
        float spread(int segment, float back) {
            return segment == TIP ? swingEnvelope(swingAge - back - 0.7, s0Tip) : swingEnvelope(swingAge - back, s0Middle);
        }
    }

    private record Swing(long start, InteractionHand hand, int count, float s0Tip, float s0Middle) {
        float spread(int segment, double age) {
            return segment == TIP ? swingEnvelope(age - 0.7, s0Tip) : swingEnvelope(age, s0Middle);
        }
    }

    private record Seen(boolean swinging, int swingTime) {
    }

    private static final class Scatter {
        final long start;
        boolean chimed;

        Scatter(long start) {
            this.start = start;
        }
    }

    private static volatile Models models;
    private static final Deque<LivingEntity> RENDERING = new ArrayDeque<>();
    private static final Map<Integer, Seen> SEEN = new HashMap<>();
    private static final Map<Integer, Swing> SWINGS = new HashMap<>();
    private static final Map<Integer, Scatter> SCATTERS = new HashMap<>();
    private static final RandomSource RANDOM = RandomSource.create();

    private ElsewhereClient() {
    }

    static ResourceLocation model(String name) {
        return new ResourceLocation(DragonsteelSchools.MODID, "item/" + name);
    }

    /** Every model to bake: the shards (with their glow layers) and the hilt. */
    static List<ResourceLocation> modelLocations() {
        List<ResourceLocation> out = new ArrayList<>();
        for (int i = 0; i < ElsewhereShards.NAMES.length; i++) {
            out.add(model(ElsewhereShards.NAMES[i]));
            if (ElsewhereShards.GLOW[i]) {
                out.add(model(ElsewhereShards.NAMES[i] + "_glow"));
            }
        }
        out.add(model("elsewhere_hilt"));
        out.add(model("elsewhere_hilt_glow"));
        return out;
    }

    /** The baked models, or null before baking (or if any failed to load). */
    static Models models() {
        return models;
    }

    /** The living entity whose render is in progress, or null outside one (first person, GUI). */
    static LivingEntity renderingEntity() {
        return RENDERING.peek();
    }

    /** This holder's motion, for the blade drawn in this hand. */
    static State state(LivingEntity holder, InteractionHand hand) {
        Swing swing = SWINGS.get(holder.getId());
        Scatter scatter = SCATTERS.get(holder.getId());
        if (swing == null && scatter == null) {
            return State.NONE;
        }
        boolean mine = swing != null && swing.hand() == hand;
        return new State(mine ? age(swing.start()) : Double.MAX_VALUE, mine ? swing.s0Tip() : 0F, mine ? swing.s0Middle() : 0F,
                mine && swing.count() % 2 == 0 ? -1 : 1, scatter == null ? Double.MAX_VALUE : age(scatter.start));
    }

    /**
     * From ElsewhereScatterPacket: this entity's Elsewhere has just carried it out of a projectile's path from
     * (x, y, z). The blade shatters in the hand; the world shows it breaking where the wielder stood.
     */
    public static void scatter(int entityId, double x, double y, double z) {
        Minecraft mc = Minecraft.getInstance();
        ClientLevel level = mc.level;
        if (level == null) {
            return;
        }
        SCATTERS.put(entityId, new Scatter(level.getGameTime()));
        Entity entity = level.getEntity(entityId);
        double height = entity == null ? 1.0 : entity.getBbHeight() * 0.6;
        ItemParticleOption shard = new ItemParticleOption(ParticleTypes.ITEM, new ItemStack(ModItems.SWORD.get(SchoolSteel.ENDER).get()));
        burst(level, shard, x, y + height, z, 26, 0.22, 0.42, 0.06);                // the blade's own fragments, every way
        burst(level, ParticleTypes.END_ROD, x, y + height, z, 14, 0.10, 0.26, 0.0);  // sparks of its edge of light
        burst(level, ParticleTypes.REVERSE_PORTAL, x, y + height, z, 40, 0.05, 0.2, 0.0);
        if (entity != null) {   // where they land: an enderman's motes
            for (int i = 0; i < 32; i++) {
                level.addParticle(ParticleTypes.PORTAL, entity.getRandomX(0.6), entity.getRandomY(), entity.getRandomZ(0.6),
                        (RANDOM.nextDouble() - 0.5) * 2.0, -RANDOM.nextDouble(), (RANDOM.nextDouble() - 0.5) * 2.0);
            }
        }
        level.playLocalSound(x, y + height, z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.PLAYERS, 1.0F, 1.2F, false);
    }

    /** count particles flung from (x, y, z) in evenly random directions at speeds between slow and fast. */
    private static void burst(ClientLevel level, net.minecraft.core.particles.ParticleOptions particle, double x, double y, double z,
                              int count, double slow, double fast, double lift) {
        for (int i = 0; i < count; i++) {
            double dx = RANDOM.nextGaussian();
            double dy = RANDOM.nextGaussian();
            double dz = RANDOM.nextGaussian();
            double speed = (slow + (fast - slow) * RANDOM.nextDouble()) / Math.max(1.0E-4, Math.sqrt(dx * dx + dy * dy + dz * dz));
            level.addParticle(particle, x, y, z, dx * speed, dy * speed + lift, dz * speed);
        }
    }

    static float swingEnvelope(double a, float s0) {
        if (a < 0.0) {
            return s0;   // before this swing (the tip's lag, an afterimage): where the last swing left it
        }
        if (a < 2.0) {
            return s0 + (1F - s0) * easeOut(a / 2.0);
        }
        if (a < 6.0) {
            return 1F;
        }
        if (a < 11.0) {
            double u = (a - 6.0) / 5.0;
            return (float) (1.0 - u * u * (1.6 - 0.6 * u));
        }
        if (a < SWING_TICKS) {   // the settle leaves the return at the same speed, so there is no kink
            double r = a - 11.0;
            return (float) (-0.224 * Math.exp(-r / 2.2) * Math.sin(1.25 * r) * (1.0 - Math.pow(r / 6.0, 4)));
        }
        return 0F;
    }

    /** How far a shard has flown (0 home, 1 out; drifts a little past 1): a burst, a drift, a staggered recall. */
    static float flight(double a, float stagger) {
        if (a <= 0.0) {
            return 0F;
        }
        if (a < BURST) {
            return easeOut(a / BURST);
        }
        double driftEnd = HANG + stagger;
        if (a < driftEnd) {
            return (float) (1.0 + 0.012 * (a - BURST));
        }
        double r = a - driftEnd;
        if (r < RETURN) {
            return (float) ((1.0 + 0.012 * (driftEnd - BURST)) * (1.0 - easeInOut(r / RETURN)));
        }
        return 0F;
    }

    /** 0 until a shard is called home, rising to 1 as it arrives: drives the spiral of its way back. */
    static float recall(double a, float stagger) {
        double r = a - (HANG + stagger);
        return r <= 0.0 ? 0F : r >= RETURN ? 1F : easeInOut(r / RETURN);
    }

    /** The little rock (degrees) of a shard that has just clicked home. */
    static float wobble(double a, float stagger) {
        double r = a - (HANG + stagger + RETURN);
        if (r < 0.0 || r > 6.0) {
            return 0F;
        }
        return (float) (12.0 * Math.exp(-r / 1.6) * Math.sin(2.4 * r));
    }

    /** The light tying a flying shard to the Eye: faint as it flies, brighter as it is drawn home. */
    static float tether(double a, float stagger) {
        double recall = HANG + stagger;
        if (a <= 0.0 || a >= recall + RETURN) {
            return 0F;
        }
        if (a < recall) {
            return (float) (0.3 * Math.min(1.0, a / 1.5));
        }
        return (float) (0.3 + 0.6 * (a - recall) / RETURN);
    }

    static float easeOut(double x) {
        double k = 1.0 - x;
        return (float) (1.0 - k * k * k);
    }

    static float easeInOut(double x) {
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
     * Spots each new swing of an Elsewhere (a wielder that has started swinging, or whose swing restarted, with the
     * blade in the swinging hand), and rings the chime as a shatter's shards come home.
     */
    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        ClientLevel level = mc.level;
        if (level == null) {
            SEEN.clear();
            SWINGS.clear();
            SCATTERS.clear();
            return;
        }
        long now = level.getGameTime();
        Item blade = ModItems.SWORD.get(SchoolSteel.ENDER).get();
        Set<Integer> wielders = new HashSet<>();
        for (Entity entity : level.entitiesForRendering()) {
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
                boolean carry = last != null && last.hand() == living.swingingArm;
                SWINGS.put(id, new Swing(now, living.swingingArm, last == null ? 1 : last.count() + 1,
                        carry ? last.spread(TIP, now - last.start()) : 0F, carry ? last.spread(MIDDLE, now - last.start()) : 0F));
            }
        }
        for (Map.Entry<Integer, Scatter> entry : SCATTERS.entrySet()) {
            Scatter scatter = entry.getValue();
            if (!scatter.chimed && now - scatter.start >= CHIME_AT) {
                scatter.chimed = true;
                Entity entity = level.getEntity(entry.getKey());
                if (entity != null) {
                    level.playLocalSound(entity.getX(), entity.getY() + entity.getBbHeight() * 0.6, entity.getZ(),
                            SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.4F, 1.1F, false);
                }
            }
        }
        SEEN.keySet().retainAll(wielders);
        SWINGS.values().removeIf(swing -> now - swing.start() > 4L * SWING_TICKS || swing.start() > now);
        SCATTERS.values().removeIf(scatter -> now - scatter.start > 2L * SCATTER_TICKS || scatter.start > now);
    }

    @SubscribeEvent
    public static void onLogout(ClientPlayerNetworkEvent.LoggingOut event) {
        SEEN.clear();
        SWINGS.clear();
        SCATTERS.clear();
        RENDERING.clear();
    }

    @Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Bake {
        private Bake() {
        }

        @SubscribeEvent
        public static void register(ModelEvent.RegisterAdditional event) {
            for (ResourceLocation location : modelLocations()) {
                event.register(location);
            }
        }

        @SubscribeEvent
        public static void bake(ModelEvent.ModifyBakingResult event) {
            Map<ResourceLocation, BakedModel> baked = event.getModels();
            BakedModel missing = baked.get(ModelBakery.MISSING_MODEL_LOCATION);
            BakedModel flat = baked.get(ITEM_MODEL);
            for (ResourceLocation location : modelLocations()) {
                BakedModel model = baked.get(location);
                if (model == null || model == missing) {
                    DragonsteelSchools.LOG.warn("Elsewhere: model {} did not load; the blade stays flat in the hand", location);
                    models = null;
                    return;
                }
            }
            if (flat == null || flat == missing) {
                models = null;
                return;
            }
            int n = ElsewhereShards.NAMES.length;
            BakedModel[] shard = new BakedModel[n];
            BakedModel[] shardGlow = new BakedModel[n];
            for (int i = 0; i < n; i++) {
                shard[i] = baked.get(model(ElsewhereShards.NAMES[i]));
                shardGlow[i] = ElsewhereShards.GLOW[i] ? baked.get(model(ElsewhereShards.NAMES[i] + "_glow")) : null;
            }
            models = new Models(baked.get(model("elsewhere_hilt")), baked.get(model("elsewhere_hilt_glow")), shard, shardGlow);
            baked.put(ITEM_MODEL, new ElsewhereBakedModel(flat));
        }
    }
}
