
// Source: http://files.acams.org/pdfs/English_Study_Guide/Chapter_5.pdf
// Suspicious transactions which may lead to money laundering
// - Unusually high monthly balances in comparison to known sources of income.
// - Unusually large deposits, deposits in round numbers or deposits in repeated amounts that are not attributable to legitimate sources of income.
// - Multiple deposits made under reportable thresholds.
// - The timing of deposits. This is particularly important when dates of illegal payments are known.
// - Checks written for unusually large amounts (in relation to the suspect's known practices).
// - A lack of account activity. This might indicate transactions in currency or the existence of other unknown bank accounts.
//
// Note: No specific bank models are used for this fraud transaction model class.

package amlsim.model.aml;

import amlsim.Account;
import amlsim.Alert;
import amlsim.model.AbstractTransactionModel;

/**
 * Suspicious transaction models
 */
public abstract class AMLTypology extends AbstractTransactionModel {

    // Fraud transaction model ID
    public static final int AML_FAN_OUT = 1;
    public static final int AML_FAN_IN = 2;
    public static final int CYCLE = 3;
    public static final int BIPARTITE = 4;
    public static final int STACK = 5;
    public static final int DENSE = 6;
    public static final int SCATTER_GATHER = 7;  // fan-out -> fan-in
    public static final int GATHER_SCATTER = 8;  // fan-in -> fan-out

    protected final float MARGIN_RATIO = 0.1F;  // Each member will keep this ratio of the received amount

    /**
     * Create an AML typology object (alert transaction model)
     * @param modelID Alert transaction model ID as int
     * @param minAmount Minimum transaction amount
     * @param maxAmount Maximum transaction amount
     * @param startStep Start step
     * @param endStep End step
     * @return Fraud transaction model object
     */
    public static AMLTypology getModel(int modelID, float minAmount, float maxAmount,
                                       int startStep, int endStep){
        AMLTypology model;
        switch(modelID){
            case AML_FAN_OUT: model = new FanOutTypology(minAmount, maxAmount, startStep, endStep); break;
            case AML_FAN_IN: model = new FanInTypology(minAmount, maxAmount, startStep, endStep); break;
            case CYCLE: model = new CycleTypology(minAmount, maxAmount, startStep, endStep); break;
            case BIPARTITE: model = new BipartiteTypology(minAmount, maxAmount, startStep, endStep); break;
            case STACK: model = new StackTypology(minAmount, maxAmount, startStep, endStep); break;
            case DENSE: model = new RandomTypology(minAmount, maxAmount, startStep, endStep); break;
            case SCATTER_GATHER: model = new ScatterGatherTypology(minAmount, maxAmount, startStep, endStep); break;
            case GATHER_SCATTER: model = new GatherScatterTypology(minAmount, maxAmount, startStep, endStep); break;
            default: throw new IllegalArgumentException("Unknown typology model ID: " + modelID);
        }
        model.setParameters(minAmount, startStep, endStep);
        return model;
    }

    Alert alert;
    protected float minAmount;
    protected float maxAmount;
    protected long startStep;
    protected long endStep;

    /**
     * Set parameters (timestamps and amounts) of transactions
     * @param modelID Scheduling model ID
     */
    public abstract void setParameters(int modelID);

    /**
     * Get the number of total transactions in this alert
     * @return Number of transactions
     */
    public abstract int getNumTransactions();

    /**
     * Bind this alert transaction model to the alert
     * @param ag Alert object
     */
    public void setAlert(Alert ag){
        this.alert = ag;
    }

    /**
     * Whether the current simulation step is within the valid simulation step range
     * @param step Current simulation step
     * @return If the current step is within the valid simulation step range, return true
     */
    public boolean isValidStep(long step){
        return startStep <= step && step <= endStep;
    }


    public int getStepRange(){
        return (int)(endStep - startStep + 1);
    }

    /**
     * Common constructor of AML typology transaction
     * @param minAmount Minimum transaction amount
     * @param maxAmount Maximum transaction amount
     * @param startStep Start simulation step of alert transactions (any transactions cannot be carried out before this step)
     * @param endStep End simulation step of alert transactions (any transactions cannot be carried out after this step)
     */
    public AMLTypology(float minAmount, float maxAmount, int startStep, int endStep){
        this.minAmount = minAmount;
        this.maxAmount = maxAmount;
        this.startStep = startStep;
        this.endStep = endStep;
    }

    /**
     * Update the minimum transaction amount if the given amount is smaller than the current one
     * @param minAmount New minimum amount
     */
    public void updateMinAmount(float minAmount){
        this.minAmount = Math.min(this.minAmount, minAmount);
    }

    /**
     * Update the maximum transaction amount if the given amount is larger than the current one
     * @param maxAmount New maximum amount
     */
    public void updateMaxAmount(float maxAmount){
        this.maxAmount = Math.max(this.maxAmount, maxAmount);
    }

    /**
     * Generate a random amount
     * @return A random amount within "minAmount" and "maxAmount"
     */
    protected float getAmount(){
        return alert.getSimulator().random.nextFloat() * (maxAmount - minAmount) + minAmount;
    }

//    /**
//     * Generate a rounded random amount
//     * @param base Multiple amount to round amount
//     * @return Rounded random amount
//     */
//    protected float getRoundedAmount(int base){
//        if(base <= 0){
//            throw new IllegalArgumentException("The base must be positive");
//        }
//        float amount = getAmount();
//        int rounded = Math.round(amount);
//        return (float)(rounded / base) * base;
//    }

    /**
     * Generate a random simulation step
     * @return A simulation step within startStep and endStep
     */
    protected long getRandomStep(){
        return alert.getSimulator().random.nextLong(getStepRange()) + startStep;
    }

    protected long getRandomStepRange(long start, long end){
        long range = end - start + 1;
        return alert.getSimulator().random.nextLong(range) + start;
    }


    @Override
    public String getType() {
        return "AMLTypology";
    }

    @Override
    public final void sendTransaction(long step) {
    }

    public abstract void sendTransactions(long step, Account acct);

}