package dev.dragonsteelschools.forge;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.cauldron.SchoolCauldrons;
import dev.dragonsteelschools.config.DSConfig;
import dev.dragonsteelschools.school.SchoolSteel;
import io.redspace.ironsspellbooks.api.events.SpellOnCastEvent;
import io.redspace.ironsspellbooks.api.events.SpellPreCastEvent;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/**
 * Where a spell of a dragonsteel school lands. Iron's Spells 3.16.3 fires {@link SpellPreCastEvent} when a cast
 * begins and {@link SpellOnCastEvent} on the server when it completes (after a long windup; for instant spells on the
 * next tick), for every cast source: spellbook, scroll, staff or imbued weapon. The spell still goes off as normal.
 * <ul>
 *   <li>Any spell of the school, aimed at a cauldron of dragon's breath, brews that school's dragon blood.</li>
 *   <li>A finishing cast of the school ({@link FinishingRule}: a Legendary cast or an Apex spell by default), aimed at a
 *   dragon forge, finishes the school's breath-tempered steel. The forge may be aimed at when the cast begins or when
 *   it completes, so a caster may look away during a long windup such as Reckoning's. Any other spell of the school
 *   aimed at a forge holding its tempered steel only earns a hint naming what is needed.</li>
 * </ul>
 */
@Mod.EventBusSubscriber(modid = DragonsteelSchools.MODID)
public final class SpellCasts {
    /** The block each caster was aiming at when their current finishing cast began. Server thread only. */
    private static final Map<UUID, GlobalPos> APEX_AIM = new HashMap<>();

    private SpellCasts() {
    }

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void onPreCast(SpellPreCastEvent event) {
        if (event.isCanceled() || !(event.getEntity() instanceof ServerPlayer caster)
                || !FinishingRule.finishes(event.getSpellId(), event.getSpellLevel(), FinishingRule.active())) {
            return;
        }
        Optional<BlockHitResult> hit = CastAim.blockInSight(caster, DSConfig.get(DSConfig.FINISHING_RANGE));
        if (hit.isPresent()) {
            APEX_AIM.put(caster.getUUID(), GlobalPos.of(caster.level().dimension(), hit.get().getBlockPos()));
        } else {
            APEX_AIM.remove(caster.getUUID());
        }
    }

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void onCast(SpellOnCastEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer caster) || event.getSchoolType() == null) {
            return;
        }
        GlobalPos aimedAtStart = APEX_AIM.remove(caster.getUUID());
        Optional<SchoolSteel> school = SchoolSteel.bySchool(event.getSchoolType().getId());
        if (event.isCanceled() || school.isEmpty()) {
            return;
        }
        FinishingRule rule = FinishingRule.active();
        boolean finisher = FinishingRule.finishes(event.getSpellId(), event.getSpellLevel(), rule);
        double cauldronRange = DSConfig.get(DSConfig.CAULDRON_RANGE);
        double range = Math.max(cauldronRange, DSConfig.get(DSConfig.FINISHING_RANGE));
        Optional<BlockHitResult> hit = CastAim.blockInSight(caster, range);
        if (hit.isPresent()) {
            BlockPos pos = hit.get().getBlockPos();
            boolean nearEnough = caster.getEyePosition().distanceToSqr(Vec3.atCenterOf(pos)) <= sq(cauldronRange + 1);
            if (nearEnough && SchoolCauldrons.tryAttune(caster, caster.serverLevel(), pos, school.get())) {
                return;
            }
            if (finisher && ApexForging.tryForge(caster, caster.serverLevel(), pos, school.get()) != ApexForging.Outcome.NOT_A_FORGE) {
                return;
            }
            if (!finisher && ApexForging.holdsTempered(caster.serverLevel(), pos, school.get())) {
                caster.displayClientMessage(Component.translatable("message.dragonsteel_schools.forge.needs." + rule.langSuffix(),
                        school.get().displayName()), true);
                return;
            }
        }
        if (finisher && aimedAtStart != null && aimedAtStart.dimension().equals(caster.level().dimension())
                && caster.getEyePosition().distanceToSqr(Vec3.atCenterOf(aimedAtStart.pos())) <= sq(DSConfig.get(DSConfig.FINISHING_RANGE) + 2)) {
            ApexForging.tryForge(caster, caster.serverLevel(), aimedAtStart.pos(), school.get());
        }
    }

    private static double sq(double value) {
        return value * value;
    }

    @SubscribeEvent
    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        APEX_AIM.remove(event.getEntity().getUUID());
    }

    @SubscribeEvent
    public static void onServerStopped(ServerStoppedEvent event) {
        APEX_AIM.clear();
    }
}
