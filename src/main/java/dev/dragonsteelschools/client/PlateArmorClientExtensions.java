package dev.dragonsteelschools.client;

import dev.dragonsteelschools.DragonsteelSchools;
import dev.dragonsteelschools.item.SchoolPlateArmorItem;
import dev.dragonsteelschools.school.SchoolSteel;
import io.redspace.ironsspellbooks.entity.armor.GenericCustomArmorRenderer;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;
import org.jetbrains.annotations.NotNull;
import software.bernie.geckolib.model.GeoModel;
import software.bernie.geckolib.renderer.GeoArmorRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/** Client half of the plate armour: Iron's GeckoLib armour renderer plus a full-bright glow-mask layer. */
public final class PlateArmorClientExtensions implements IClientItemExtensions {
    private final SchoolSteel school;
    private GeoArmorRenderer<SchoolPlateArmorItem> renderer;

    public PlateArmorClientExtensions(SchoolSteel school) {
        this.school = school;
    }

    @Override
    public @NotNull HumanoidModel<?> getHumanoidArmorModel(LivingEntity entity, ItemStack stack, EquipmentSlot slot, HumanoidModel<?> original) {
        if (renderer == null) {
            GenericCustomArmorRenderer<SchoolPlateArmorItem> made = new GenericCustomArmorRenderer<>(new Model(school));
            made.addRenderLayer(new AutoGlowingGeoLayer<>(made));
            renderer = made;
        }
        renderer.prepForRender(entity, stack, slot, original);
        return renderer;
    }

    static final class Model extends GeoModel<SchoolPlateArmorItem> {
        private final ResourceLocation geo;
        private final ResourceLocation texture;
        private final ResourceLocation animation;

        Model(SchoolSteel school) {
            this.geo = new ResourceLocation(DragonsteelSchools.MODID, "geo/" + school.id() + "_dragonsteel_plate.geo.json");
            this.texture = new ResourceLocation(DragonsteelSchools.MODID, "textures/models/armor/" + school.id() + "_dragonsteel_plate.png");
            this.animation = new ResourceLocation(DragonsteelSchools.MODID, "animations/dragonsteel_plate.animation.json");
        }

        @Override
        public ResourceLocation getModelResource(SchoolPlateArmorItem item) {
            return geo;
        }

        @Override
        public ResourceLocation getTextureResource(SchoolPlateArmorItem item) {
            return texture;
        }

        @Override
        public ResourceLocation getAnimationResource(SchoolPlateArmorItem item) {
            return animation;
        }
    }
}
