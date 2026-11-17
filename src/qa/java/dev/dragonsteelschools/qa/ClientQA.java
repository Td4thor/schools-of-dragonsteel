package dev.dragonsteelschools.qa;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.registry.ModRegistries;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.Consumer;

/**
 * Dev-only client smoke harness and armour showcase:
 * {@code bash tools/run_client_qa.sh} (runs {@code gradlew runClient -Pdsqa -PdsqaWorld=QA}).
 * <ol>
 *   <li>Screenshots the world as loaded, HUD and bare arm included (the 0.1.0-dev.1 crash path).</li>
 *   <li>For each school: four armour stands on a sky platform at noon (front, three-quarter, side, back), then a
 *   close front and close back, with FOV 30 so the armour fills the frame; then the player in the full kit in first
 *   person and third person (sword in the main hand, axe in the off hand; Holy also burning with holy fire).
 *   Ender also shoots Elsewhere mid-swing and mid-scatter in both views (the moving in-hand blade).</li>
 * </ol>
 * Screenshots go to run/screenshots. Logs "[DragonsteelSchools/qa] DONE" and quits.
 */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID, value = Dist.CLIENT)
public final class ClientQA {
    private static final boolean ENABLED = Boolean.getBoolean("dragonsteel_schools.qa");
    private static final List<Step> STEPS = new ArrayList<>();
    private static int ticksInWorld;
    /** True while the JEI steps run: their shots are of screens, so an open screen must not stall the harness. */
    private static boolean screensAllowed;
    private static int stepIndex;
    private static int waitUntil;
    private static int shots;
    /** Platform origin, fixed from the player's position when the stage is built. */
    private static BlockPos base;

    private record Step(int delay, String name, Consumer<Minecraft> action) {
    }

    static {
        add(80, "as_loaded", mc -> shot(mc, "00_as_loaded_first_person"));
        add(5, "stage", mc -> onServer(mc, player -> {
            base = player.blockPosition().above(40);
            run(player, "time set 6000");
            run(player, "weather clear");
            run(player, "gamerule doDaylightCycle false");
            run(player, "gamemode creative @a");   // the command source is the server, so name the target
            // the QA save is a throwaway copy: clear mobs and items near the stage so their particles stay out of shot
            run(player, "kill @e[type=!minecraft:player,distance=..128]");
            run(player, fill(-5, 0, -2, 5, 0, 2, "minecraft:smooth_quartz"));
            player.getAbilities().flying = true;
            player.onUpdateAbilities();
        }));
        add(1, "no_tutorial", mc -> {   // the "Move with W, A, S and D" toast stays out of the gallery shots
            mc.options.tutorialStep = net.minecraft.client.tutorial.TutorialSteps.NONE;
            mc.getTutorial().setStep(net.minecraft.client.tutorial.TutorialSteps.NONE);
            mc.getToasts().clear();
        });
        add(300, "settle", mc -> { });   // let teleport and chunk particles die away before the first lineup
        String only = System.getProperty("dragonsteel_schools.qa.schools", "");
        for (SchoolSteel school : SchoolSteel.values()) {
            String s = school.id();
            if (!only.isBlank() && !java.util.Arrays.asList(only.split(",")).contains(s)) {
                continue;
            }
            add(10, s + "_stands", mc -> onServer(mc, player -> {
                // move old stands out of sight before killing them, so their death smoke stays off camera
                run(player, "tp @e[type=minecraft:armor_stand,tag=dsqa] ~ -200 ~");
                run(player, "kill @e[type=minecraft:armor_stand,tag=dsqa]");
                double[] xs = {-2.25, -0.75, 0.75, 2.25};
                float[] yaws = {0, 45, 90, 180};
                for (int i = 0; i < 4; i++) {
                    run(player, stand(school, base.getX() + 0.5 + xs[i], base.getY() + 1, base.getZ() + 0.5, yaws[i]));
                }
                look(player, base.getX() + 0.5, base.getY() + 1, base.getZ() + 0.5 + 8.5, 180, 4);
            }));
            add(5, s + "_lineup_camera", mc -> camera(mc, CameraType.FIRST_PERSON, true, 30));
            add(40, s + "_lineup", mc -> shot(mc, s + "_1_lineup"));
            add(5, s + "_close_front_pos", mc -> onServer(mc, player ->
                    look(player, base.getX() + 0.5 - 2.25, base.getY() + 1, base.getZ() + 0.5 + 4.8, 180, 5)));
            add(20, s + "_close_front", mc -> shot(mc, s + "_2_close_front"));
            add(5, s + "_close_back_pos", mc -> onServer(mc, player ->
                    look(player, base.getX() + 0.5 + 2.25, base.getY() + 1, base.getZ() + 0.5 + 4.8, 180, 5)));
            add(20, s + "_close_back", mc -> shot(mc, s + "_3_close_back"));
            add(5, s + "_kit", mc -> onServer(mc, player -> {
                player.setItemSlot(EquipmentSlot.HEAD, new ItemStack(ModItems.HELMET.get(school).get()));
                player.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModItems.CHESTPLATE.get(school).get()));
                player.setItemSlot(EquipmentSlot.LEGS, new ItemStack(ModItems.LEGGINGS.get(school).get()));
                player.setItemSlot(EquipmentSlot.FEET, new ItemStack(ModItems.BOOTS.get(school).get()));
                player.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(ModItems.SWORD.get(school).get()));
                player.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(ModItems.AXE.get(school).get()));
                if (school == SchoolSteel.HOLY) {
                    player.addEffect(new MobEffectInstance(ModRegistries.HOLY_FIRE.get(), 20 * 30, 0, false, false, true));
                } else {
                    player.removeEffect(ModRegistries.HOLY_FIRE.get());
                }
                look(player, base.getX() + 0.5, base.getY() + 1, base.getZ() + 0.5 + 6, 0, 0);
            }));
            add(5, s + "_first_person_camera", mc -> camera(mc, CameraType.FIRST_PERSON, false, 70));
            add(30, s + "_first_person", mc -> shot(mc, s + "_4_first_person"));
            if (school == SchoolSteel.ENDER) {
                elsewhereShots(s, "4");
            }
            add(5, s + "_third_person_camera", mc -> camera(mc, CameraType.THIRD_PERSON_FRONT, true, 50));
            add(20, s + "_third_person", mc -> shot(mc, s + "_5_third_person" + (school == SchoolSteel.HOLY ? "_holy_fire" : "")));
            if (school == SchoolSteel.ENDER) {
                elsewhereShots(s, "5");
            }
        }
        if (net.minecraftforge.fml.ModList.get().isLoaded("jei")) {   // the mod's JEI pages
            add(10, "jei_finishing", mc -> {
                screensAllowed = true;
                QaJei.showType(true);
            });
            add(20, "jei_finishing_shot", mc -> shot(mc, "jei_1_finishing"));
            add(5, "jei_blood", mc -> QaJei.showType(false));
            add(20, "jei_blood_shot", mc -> shot(mc, "jei_2_blood"));
            add(5, "jei_info_tempered", mc -> QaJei.showInfo(ModItems.TEMPERED.get(SchoolSteel.HOLY).get()));
            add(20, "jei_info_tempered_shot", mc -> shot(mc, "jei_3_info_tempered"));
            add(5, "jei_info_elsewhere", mc -> QaJei.showInfo(ModItems.SWORD.get(SchoolSteel.ENDER).get()));
            add(20, "jei_info_elsewhere_shot", mc -> shot(mc, "jei_4_info_elsewhere"));
            add(5, "jei_close", mc -> {
                screensAllowed = false;
                mc.setScreen(null);
            });
        }
        add(10, "done", mc -> {
            DragonsteelSchools.LOG.info("[DragonsteelSchools/qa] DONE: {} screenshots", shots);
            mc.stop();
        });
    }

    private ClientQA() {
    }

    /**
     * Elsewhere's in-hand blade mid-swing (3 ticks in) and with the arm back while the pieces are still apart (8
     * ticks in); then a dodge's shatter at its widest (3 ticks), as the shards are drawn home (13) and settling (19),
     * with the world burst set 2.5 blocks ahead so it is in shot; then at rest.
     */
    private static void elsewhereShots(String s, String view) {
        add(10, s + "_" + view + "_swing", mc -> mc.player.swing(InteractionHand.MAIN_HAND));
        add(3, s + "_" + view + "_swing_shot", mc -> shot(mc, s + "_" + view + "b_elsewhere_swing"));
        add(5, s + "_" + view + "_swing_held_shot", mc -> shot(mc, s + "_" + view + "b2_elsewhere_swing_held"));
        add(20, s + "_" + view + "_scatter", mc -> {
            // the burst goes where the camera looks, 3 blocks out (scatter lifts it by 0.6 of the player's height)
            net.minecraft.world.phys.Vec3 at = mc.gameRenderer.getMainCamera().getPosition()
                    .add(new net.minecraft.world.phys.Vec3(mc.gameRenderer.getMainCamera().getLookVector()).scale(3.0))
                    .subtract(0.0, mc.player.getBbHeight() * 0.6, 0.0);
            mc.options.particles().set(net.minecraft.client.ParticleStatus.ALL);   // the burst is particles; the QA runs on minimal
            dev.dragonsteelschools.client.ElsewhereClient.scatter(mc.player.getId(), at.x, at.y, at.z);
        });
        add(3, s + "_" + view + "_scatter_shot", mc -> shot(mc, s + "_" + view + "c_elsewhere_scatter"));
        add(10, s + "_" + view + "_recall_shot", mc -> shot(mc, s + "_" + view + "c2_elsewhere_recall"));
        add(6, s + "_" + view + "_settle_shot", mc -> shot(mc, s + "_" + view + "c3_elsewhere_settle"));
        add(30, s + "_" + view + "_rest_shot", mc -> {
            mc.options.particles().set(net.minecraft.client.ParticleStatus.MINIMAL);
            shot(mc, s + "_" + view + "d_elsewhere_rest");
        });
    }

    private static void add(int delay, String name, Consumer<Minecraft> action) {
        STEPS.add(new Step(delay, name, action));
    }

    private static String fill(int x0, int y0, int z0, int x1, int y1, int z1, String block) {
        return String.format(Locale.ROOT, "fill %d %d %d %d %d %d %s", base.getX() + x0, base.getY() + y0, base.getZ() + z0,
                base.getX() + x1, base.getY() + y1, base.getZ() + z1, block);
    }

    private static String id(RegistryObject<Item> item) {
        return ForgeRegistries.ITEMS.getKey(item.get()).toString();
    }

    private static String stand(SchoolSteel school, double x, double y, double z, float yaw) {
        String armour = String.format(Locale.ROOT, "[{id:\"%s\",Count:1b},{id:\"%s\",Count:1b},{id:\"%s\",Count:1b},{id:\"%s\",Count:1b}]",
                id(ModItems.BOOTS.get(school)), id(ModItems.LEGGINGS.get(school)),
                id(ModItems.CHESTPLATE.get(school)), id(ModItems.HELMET.get(school)));
        return String.format(Locale.ROOT,
                "summon minecraft:armor_stand %.2f %.2f %.2f {Tags:[\"dsqa\"],NoGravity:1b,Invulnerable:1b,ShowArms:1b,NoBasePlate:1b,"
                        + "Rotation:[%.1ff,0f],ArmorItems:%s}", x, y, z, yaw, armour);
    }

    private static void look(ServerPlayer player, double x, double y, double z, float yaw, float pitch) {
        player.teleportTo(player.serverLevel(), x, y, z, yaw, pitch);
    }

    private static void camera(Minecraft mc, CameraType type, boolean hideGui, int fov) {
        mc.options.cloudStatus().set(net.minecraft.client.CloudStatus.OFF);
        mc.options.particles().set(net.minecraft.client.ParticleStatus.MINIMAL);
        mc.options.setCameraType(type);
        mc.options.hideGui = hideGui;
        mc.options.fov().set(fov);
    }

    private static void run(ServerPlayer player, String command) {
        player.server.getCommands().performPrefixedCommand(player.server.createCommandSourceStack().withSuppressedOutput(), command);
    }

    private static void shot(Minecraft mc, String name) {
        shots++;
        Screenshot.grab(mc.gameDirectory, "ds_qa_" + name + ".png", mc.getMainRenderTarget(),
                message -> DragonsteelSchools.LOG.info("[DragonsteelSchools/qa] {}", message.getString()));
    }

    private static void onServer(Minecraft mc, Consumer<ServerPlayer> action) {
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null || mc.player == null) {
            throw new IllegalStateException("QA harness needs a singleplayer world");
        }
        server.execute(() -> {
            ServerPlayer player = server.getPlayerList().getPlayer(mc.player.getUUID());
            if (player != null) {
                action.accept(player);
            }
        });
    }

    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (!ENABLED || event.phase != TickEvent.Phase.END) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        // Never stall behind the pause menu when the window loses focus (Tad may be using the PC meanwhile).
        mc.options.pauseOnLostFocus = false;
        if (mc.screen instanceof net.minecraft.client.gui.screens.PauseScreen) {
            mc.setScreen(null);
        }
        if (mc.player == null || mc.level == null || (mc.screen != null && !screensAllowed) || stepIndex >= STEPS.size()) {
            return;
        }
        ticksInWorld++;
        if (ticksInWorld == 1) {
            mc.options.hideGui = false;
            waitUntil = STEPS.get(0).delay();
            DragonsteelSchools.LOG.info("[DragonsteelSchools/qa] in world, wearing {}", mc.player.getItemBySlot(EquipmentSlot.CHEST));
        }
        if (ticksInWorld < waitUntil) {
            return;
        }
        Step step = STEPS.get(stepIndex++);
        DragonsteelSchools.LOG.info("[DragonsteelSchools/qa] step {}", step.name());
        step.action().accept(mc);
        if (stepIndex < STEPS.size()) {
            waitUntil = ticksInWorld + STEPS.get(stepIndex).delay();
        }
    }
}
