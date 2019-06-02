//
// Note: No specific bank models are used for this fraud transaction model class.
//

package amlsim.model.fraud;

import amlsim.Account;

/**
 * Stacked bipartite transactions
 */
public class StackTransactionModel extends FraudTransactionModel {

    @Override
    public void setSchedule(int modelID) {

    }

    public StackTransactionModel(float minAmount, float maxAmount, int minStep, int maxStep) {
        super(minAmount, maxAmount, minStep, maxStep);
    }

    @Override
    public String getType() {
        return "StackFraud";
    }

    @Override
    public void sendTransactions(long step, Account acct) {

        int total_members = alert.getMembers().size();
        int orig_members = total_members / 3;  // First 1/3 accounts are sender accounts
        int mid_members = orig_members;  // Second 1/3 accounts are intermediate accounts
        int dest_members = total_members - orig_members * 2;  // Rest of accounts are receiver accounts

        float amount1 = getAmount();
        float total_flow = amount1 * orig_members * mid_members;  // Total transaction amount
        float amount2 = total_flow / (mid_members * dest_members);

        for(int i=0; i<orig_members; i++){  // Sender accounts --> Intermediate accounts
            Account orig = alert.getMembers().get(i);
            if(!orig.getID().equals(acct.getID())){
                continue;
            }

            for(int j=orig_members; j<(orig_members+mid_members); j++){
                Account dest = alert.getMembers().get(j);
                sendTransaction(step, amount1, orig, dest);
            }
        }

        for(int i=orig_members; i<(orig_members+mid_members); i++){   // Intermediate accounts --> Receiver accounts
            Account orig = alert.getMembers().get(i);
            if(!orig.getID().equals(acct.getID())){
                continue;
            }

            for(int j=(orig_members+mid_members); j<total_members; j++){
                Account dest = alert.getMembers().get(j);
                sendTransaction(step, amount2, orig, dest);
            }
        }
    }
}
