package dev.dragonsteelschools.client;

import dev.dragonsteelschools.DragonsteelSchools;
import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.client.resources.model.ModelBakery;
import net.minecraft.client.resources.model.ModelResourceLocation;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
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
import java.util.Map;

/**
 * Client half of Elsewhere's moving blade (ElsewhereRenderer draws it).
 * <ul>
 *   <li>Bakes the six piece models (tip, middle, hilt, each with a full-bright _glow layer) and swaps Elsewhere's
 *   item model for {@link ElsewhereBakedModel}, which hands the in-hand views to the renderer.</li>
 *   <li>Remembers which living entity is being drawn, so a third-person view knows whose swing to follow.</li>
 *   <li>Keeps the time of each wielder's last dodge (ElsewhereScatterPacket), so the shards can fly apart.</li>
 * </ul>
 * If a piece model fails to load, Elsewhere simply stays the flat sprite.
 */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID, value = Dist.CLIENT)
public final class ElsewhereClient {
    static final ModelResourceLocation ITEM_MODEL =
            new ModelResourceLocation(new ResourceLocation(DragonsteelSchools.MODID, "elsewhere"), "inventory");
    /** Index order the renderer relies on: tip, tip glow, middle, middle glow, hilt, hilt glow. */
    static final ResourceLocation[] PIECE_MODELS = new ResourceLocation[6];
    /** Ticks a dodge's scatter lasts: out in two ticks, back together by the end. */
    static final double SCATTER_TICKS = 20.0;

    private static volatile BakedModel[] pieces;
    private static final Deque<LivingEntity> RENDERING = new ArrayDeque<>();
    private static final Map<Integer, Double> SCATTERS = new HashMap<>();

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
            SCATTERS.put(entityId, now(mc));
        }
    }

    /** 0..1: how far a recent dodge has flung the blade apart. Rises over 2 ticks, settles over the next 17. */
    static float scatter(LivingEntity holder) {
        Double start = SCATTERS.get(holder.getId());
        if (start == null) {
            return 0F;
        }
        double age = (now(Minecraft.getInstance()) - start) / SCATTER_TICKS;
        if (age < 0.0 || age >= 1.0) {
            return 0F;
        }
        return smooth(age / 0.1) * (1F - smooth((age - 0.15) / 0.85));
    }

    static double now(Minecraft mc) {
        return mc.level == null ? 0.0 : mc.level.getGameTime() + (double) mc.getPartialTick();
    }

    private static float smooth(double t) {
        double c = Math.max(0.0, Math.min(1.0, t));
        return (float) (c * c * (3.0 - 2.0 * c));
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

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (event.phase == TickEvent.Phase.END && !SCATTERS.isEmpty()) {
            double now = now(Minecraft.getInstance());
            SCATTERS.values().removeIf(start -> now - start > 2 * SCATTER_TICKS || start - now > 2 * SCATTER_TICKS);
        }
    }

    @SubscribeEvent
    public static void onLogout(ClientPlayerNetworkEvent.LoggingOut event) {
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
