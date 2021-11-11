//
// Note: No specific bank models are used for this AML typology model class.
//

package amlsim.model.aml;

import amlsim.AMLSim;
import amlsim.Account;
import amlsim.TargetedTransactionAmount;

import java.util.*;

/**
 * Cycle transaction model
 */
public class CycleTypology extends AMLTypology {

    // Transaction schedule
    private long[] steps;  // Array of simulation steps when each transaction is scheduled to be made

    private Random random = AMLSim.getRandom();

    CycleTypology(double minAmount, double maxAmount, int startStep, int endStep){
        super(minAmount, maxAmount, startStep, endStep);
    }

    /**
     * Define schedule of transaction
     * @param modelID Schedule model ID as integer
     */
    public void setParameters(int modelID) {
        
        List<Account> members = alert.getMembers();  // All members
        int length = members.size();  // Number of members (total transactions)
        steps = new long[length];

        int allStep = (int)AMLSim.getNumOfSteps();
        int period = (int)(endStep - startStep);
        this.startStep = generateStartStep(allStep - period);  //  decentralize the first transaction step
        this.endStep = Math.min(this.startStep + period, allStep);

        if(modelID == FIXED_INTERVAL){  // Ordered, same interval
            period = (int)(endStep - startStep);
            if(length < period){
                this.interval = period / length; // If there is enough number of available steps, make transaction with interval
                for(int i=0; i<length-1; i++){
                    steps[i] = startStep + interval * i;
                }
                steps[length-1] = endStep;
            }else{
                this.interval = 1;
                long batch = length / period;  // Because of too many transactions, make one or more transactions per step
                for(int i=0; i<length-1; i++){
                    steps[i] = startStep + i / batch;
                }
                steps[length-1] = endStep;
            }
        }else if(modelID == RANDOM_INTERVAL || modelID == UNORDERED){  // Random interval
            this.interval = 1;
            // Ensure the specified period
            steps[0] = startStep;
            steps[1] = endStep;
            for(int i=2; i<length; i++){
                steps[i] = getRandomStep();
            }
            if(modelID == RANDOM_INTERVAL){
                Arrays.sort(steps);  // Ordered
            }
        }
//        System.out.println(Arrays.toString(steps));
    }

//    @Override
//    public int getNumTransactions() {
//        return alert.getMembers().size();  // The number of transactions is the same as the number of members
//    }

    @Override
    public String getModelName() {
        return "CycleTypology";
    }

    /**
     * Create and add transactions
     * @param step Current simulation step
     */
    @Override
    public void sendTransactions(long step, Account acct) {
        int length = alert.getMembers().size();
        long alertID = alert.getAlertID();
        boolean isSAR = alert.isSAR();

        double amount = Double.MAX_VALUE;
        TargetedTransactionAmount transactionAmount;

        // Create cycle transactions
        for (int i = 0; i < length; i++) {
            if (steps[i] == step) {
                int j = (i + 1) % length; // i, j: index of the previous, next account
                Account src = alert.getMembers().get(i); // The previous account
                Account dst = alert.getMembers().get(j); // The next account

                if (src.getBalance() < amount)
                {
                    amount = src.getBalance();
                }
                transactionAmount = new TargetedTransactionAmount(amount, random);
                makeTransaction(step, transactionAmount.doubleValue(), src, dst, isSAR, alertID);

                // Update the next transaction amount
                double margin = amount * marginRatio;
                amount = amount - margin;
            }
        }
    }
}
