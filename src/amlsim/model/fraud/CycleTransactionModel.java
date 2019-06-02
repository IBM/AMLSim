//
// Note: No specific bank models are used for this fraud transaction model class.
//

package amlsim.model.fraud;

import amlsim.Account;

import java.util.*;

/**
 * Cycle transaction model
 */
public class CycleTransactionModel extends FraudTransactionModel {

    // Transaction schedule
    private long[] steps;  // Array of simulation steps when each transaction is scheduled to be made
    public static final int FIXED_INTERVAL = 0;  // All accounts send money in order with the same interval
    public static final int RANDOM_INTERVAL = 1;  // All accounts send money in order with random intervals
    public static final int UNORDERED = 2;  // All accounts send money randomly

    public CycleTransactionModel(float minAmount, float maxAmount, int minStep, int maxStep){
        super(minAmount, maxAmount, minStep, maxStep);
    }

    /**
     * Define schedule of transaction
     * @param modelID Schedule model ID as integer
     */
    public void setSchedule(int modelID){
        List<Account> members = alert.getMembers();  // All fraud transaction members
        int length = members.size();  // Number of members (total transactions)
        steps = new long[length];

        if(modelID == FIXED_INTERVAL){  // Ordered, same interval
            long range = endStep - startStep + 1;
            if(length < range){
                long interval = range / length; // If there is enough number of available steps, make transaction with interval
                for(int i=0; i<length; i++){
                    steps[i] = startStep + interval*i;
                }
            }else{
                long batch = length / range;  // Because of too many transactions, make one or more transactions per step
                for(int i=0; i<length; i++){
                    steps[i] = startStep + i/batch;
                }
            }
        }else if(modelID == RANDOM_INTERVAL || modelID == UNORDERED){  // Random interval
            for(int i=0; i<length; i++){
                steps[i] = getRandomStep();
            }
            if(modelID == RANDOM_INTERVAL){
                Arrays.sort(steps);  // Ordered
            }
        }
    }

    @Override
    public String getType() {
        return "CycleFraud";
    }

    /**
     * Create and add transactions
     * @param step Current simulation step
     */
    @Override
    public void sendTransactions(long step, Account acct) {
        int length = alert.getMembers().size();
        long alertID = alert.getAlertID();
        boolean isFraud = alert.isFraud();
        float amount = getAmount();

        // Create cycle transactions
        for(int i=0; i<length; i++){
            if(steps[i] == step){
                int j = (i+1) % length;  // i, j: index of the previous, next account
                Account src = alert.getMembers().get(i);  // The previous account
                Account dst = alert.getMembers().get(j);  // The next account
                if(src.getID().equals(acct.getID())) {
                    sendTransaction(step, amount, src, dst, isFraud, alertID);
                }
            }
        }
    }
}
