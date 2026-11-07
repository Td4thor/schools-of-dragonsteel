package dev.dragonsteelschools.qa;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.registry.ModItems;
import dev.dragonsteelschools.registry.ModRegistries;
import dev.dragonsteelschools.school.SchoolSteel;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * Dev-only client smoke harness: {@code gradlew runClient -Pdsqa -PdsqaWorld="<save in run/saves>"}.
 * Waits in the loaded world, then for each school equips the full plate set, the signature sword and the staff,
 * lights holy fire on the player, and screenshots first person, third person front and back into run/screenshots.
 * Quits when done. Logs "[DragonsteelSchools/qa] DONE" so a script can tell a clean finish from a crash.
 */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID, value = Dist.CLIENT)
public final class ClientQA {
    private static final boolean ENABLED = Boolean.getBoolean("dragonsteel_schools.qa");
    private static final List<Step> STEPS = new ArrayList<>();
    private static int ticksInWorld;
    private static int stepIndex;
    private static int waitUntil;

    private record Step(int delay, String name, Consumer<Minecraft> action) {
    }

    static {
        add(80, "first_person_as_loaded", mc -> shot(mc, "00_as_loaded_first_person"));
        // Noon, clear sky, hovering in open air facing level, so third-person shots show the armour against the sky.
        add(5, "stage", mc -> onServer(mc, player -> {
            player.serverLevel().setDayTime(6000);
            player.serverLevel().setWeatherParameters(6000, 0, false, false);
            player.getAbilities().mayfly = true;
            player.getAbilities().flying = true;
            player.onUpdateAbilities();
            player.teleportTo(player.serverLevel(), player.getX(), player.getY() + 12, player.getZ(), 0.0F, 0.0F);
        }));
        for (SchoolSteel school : SchoolSteel.values()) {
            String s = school.id();
            add(10, s + "_equip", mc -> onServer(mc, player -> {
                player.setItemSlot(EquipmentSlot.HEAD, new ItemStack(ModItems.HELMET.get(school).get()));
                player.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModItems.CHESTPLATE.get(school).get()));
                player.setItemSlot(EquipmentSlot.LEGS, new ItemStack(ModItems.LEGGINGS.get(school).get()));
                player.setItemSlot(EquipmentSlot.FEET, new ItemStack(ModItems.BOOTS.get(school).get()));
                player.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(ModItems.SWORD.get(school).get()));
                player.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(ModItems.STAFF.get(school).get()));
                if (school == SchoolSteel.HOLY) {
                    player.addEffect(new MobEffectInstance(ModRegistries.HOLY_FIRE.get(), 20 * 30, 0, false, false, true));
                } else {
                    player.removeEffect(ModRegistries.HOLY_FIRE.get());
                }
            }));
            add(5, s + "_first_person_camera", mc -> {
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                mc.options.hideGui = false;   // F1 also hides the first-person hand
            });
            add(30, s + "_first_person", mc -> shot(mc, s + "_1_first_person"));
            add(5, s + "_front_camera", mc -> {
                mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
                mc.options.hideGui = true;
            });
            add(15, s + "_front", mc -> shot(mc, s + "_2_front"));
            add(5, s + "_back_camera", mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
            add(15, s + "_back", mc -> shot(mc, s + "_3_back"));
        }
        add(10, "done", mc -> {
            DragonsteelSchools.LOG.info("[DragonsteelSchools/qa] DONE: {} screenshots", SchoolSteel.values().length * 3 + 1);
            mc.stop();
        });
    }

    private ClientQA() {
    }

    private static void add(int delay, String name, Consumer<Minecraft> action) {
        STEPS.add(new Step(delay, name, action));
    }

    private static void shot(Minecraft mc, String name) {
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
        if (mc.player == null || mc.level == null || mc.screen != null || stepIndex >= STEPS.size()) {
            return;
        }
        ticksInWorld++;
        if (ticksInWorld == 1) {
            // The first shot keeps the HUD and the bare first-person arm: the 0.1.0-dev.1 crash path
            // (ItemInHandRenderer -> PlayerRenderer.renderHand -> armour model lookup).
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
