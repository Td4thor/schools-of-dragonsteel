package dev.dragonsteelschools.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraftforge.client.model.BakedModelWrapper;

/**
 * Elsewhere's item model. In the inventory, on the ground and in item frames it is the flat sprite, unchanged. In a
 * hand (first or third person) it applies the sprite's own display transform and then answers as a custom-renderer
 * model, so ItemRenderer hands the draw to ElsewhereRenderer (the trident's route, without a second model file).
 */
final class ElsewhereBakedModel extends BakedModelWrapper<BakedModel> {
    private final BakedModel inHand;

    ElsewhereBakedModel(BakedModel flat) {
        super(flat);
        this.inHand = new BakedModelWrapper<>(flat) {
            @Override
            public boolean isCustomRenderer() {
                return true;
            }
        };
    }

    @Override
    public BakedModel applyTransform(ItemDisplayContext context, PoseStack pose, boolean leftHand) {
        BakedModel flat = super.applyTransform(context, pose, leftHand);
        return switch (context) {
            case FIRST_PERSON_LEFT_HAND, FIRST_PERSON_RIGHT_HAND, THIRD_PERSON_LEFT_HAND, THIRD_PERSON_RIGHT_HAND -> inHand;
            default -> flat;
        };
    }
}
