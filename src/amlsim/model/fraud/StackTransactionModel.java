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
    public void sendTransactions(long step) {
//        ArrayList<AMLTransaction> txs = new ArrayList<>();
//        boolean isFraud = alert.isFraud();
//        long alertID = alert.getAlertID();

        int total_members = alert.getMembers().size();
        int orig_members = total_members / 3;
        int mid_members = orig_members;
        int dest_members = total_members - orig_members * 2;
        float amount1 = getAmount();
        float total_flow = amount1 * orig_members * mid_members;
        float amount2 = total_flow / (mid_members * dest_members);

        for(int i=0; i<orig_members; i++){
            Account orig = alert.getMembers().get(i);

            for(int j=orig_members; j<(orig_members+mid_members); j++){
                Account dest = alert.getMembers().get(j);
//                orig.addDest(dest);
                sendTransaction(step, amount1, orig, dest);
//                tx.setAlertID(alertID);
//                tx.setFraud(isFraud);
//                txs.add(tx);
            }
        }

        for(int i=orig_members; i<(orig_members+mid_members); i++){
            Account orig = alert.getMembers().get(i);

            for(int j=(orig_members+mid_members); j<total_members; j++){
                Account dest = alert.getMembers().get(j);

//                orig.addDest(dest);
                sendTransaction(step, amount2, orig, dest);
//                tx.setAlertID(alertID);
//                tx.setFraud(isFraud);
//                txs.add(tx);
            }
        }

//        return txs;
    }
}
