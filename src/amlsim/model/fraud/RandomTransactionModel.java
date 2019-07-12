//
// Note: No specific bank models are used for this fraud transaction model class.
//

package amlsim.model.fraud;

import amlsim.Account;

import java.util.List;

/**
 * The main account (subject account of fraud) makes a transaction with one of the neighbor accounts
 * and the neighbor also makes transactions with its neighbors
 */
public class RandomTransactionModel extends FraudTransactionModel {

    private static int count = 0;

    @Override
    public void setSchedule(int modelID) {

    }

    @Override
    public int getNumTransactions() {
        return alert.getMembers().size();
    }

    public RandomTransactionModel(float minAmount, float maxAmount, int minStep, int maxStep) {
        super(minAmount, maxAmount, minStep, maxStep);
    }

    @Override
    public String getType() {
        return "DenseFraud";
    }

    public void sendTransactions(long step, Account acct){
        boolean isFraud = alert.isFraud();
        long alertID = alert.getAlertID();
        if(!isValidStep(step))return;

        Account hub = isFraud ? alert.getSubjectAccount() : this.alert.getMembers().get(0); // Main account
        List<Account> dests = hub.getDests();
        int numDests = dests.size();
        if(numDests == 0)return;

        float amount = getAmount() / numDests;

        int idx = (int)(step % numDests);  // Choose one of neighbors
        Account dest = dests.get(idx);
        sendTransaction(step, amount, hub, dest, isFraud, (int)alertID);  // Main account makes transactions to one of the neighbors
        List<Account> nbs = dest.getDests();
        int numNbs = nbs.size();
        if(numNbs > 0){
            idx = (int)(step % numNbs);  // Choose one of its neighbors
            Account nb = nbs.get(idx);
            sendTransaction(step, amount, dest, nb, isFraud, (int)alertID);  // Neighbor accounts make transactions
        }
    }
}
