package dev.dragonsteelschools.forge;

/** How much of a slot one Apex cast can finish. Pure arithmetic, so it is unit-tested without a game. */
public final class ForgeBatchMath {
    /** One cast finishes at most a full stack. */
    public static final int MAX_PER_CAST = 64;

    private ForgeBatchMath() {
    }

    /**
     * A slot is finished whole or not at all, because the result replaces the tempered steel in the same slot.
     *
     * @param count       tempered items in the slot
     * @param budget      items this cast may still finish
     * @param resultCount result items per tempered item (usually 1)
     * @param maxStack    the result's max stack size
     * @return items consumed from the slot: {@code count}, or 0 if the slot does not fit the budget or the stack
     */
    public static int finishSlot(int count, int budget, int resultCount, int maxStack) {
        if (count <= 0 || budget <= 0 || resultCount <= 0 || maxStack <= 0) {
            return 0;
        }
        if (count > budget || (long) count * resultCount > maxStack) {
            return 0;
        }
        return count;
    }
}
