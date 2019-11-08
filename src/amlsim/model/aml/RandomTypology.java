//
// Note: No specific bank models are used for this fraud transaction model class.
//

package amlsim.model.aml;

import amlsim.Account;

import java.util.List;
import java.util.Random;

/**
 * The main account (subject account of fraud) makes a transaction with one of the neighbor accounts
 * and the neighbor also makes transactions with its neighbors.
 * The beneficiary account and amount of each transaction are determined randomly.
 */
public class RandomTypology extends AMLTypology {

    private static Random rand = new Random();

    @Override
    public void setParameters(int modelID) {

    }

    @Override
    public int getNumTransactions() {
        return alert.getMembers().size();
    }

    RandomTypology(float minAmount, float maxAmount, int minStep, int maxStep) {
        super(minAmount, maxAmount, minStep, maxStep);
    }

    @Override
    public String getType() {
        return "RandomTypology";
    }

    public void sendTransactions(long step, Account acct){
        boolean isFraud = alert.isSAR();
        long alertID = alert.getAlertID();
        if(!isValidStep(step))return;

        Account hub = isFraud ? alert.getSubjectAccount() : this.alert.getMembers().get(0); // Main account
        List<Account> beneList = hub.getDests();
        int numBenes = beneList.size();
        if(numBenes == 0)return;

        float amount = getRandomAmount();

//        int idx = (int)(step % numBenes);  // Choose one of neighbors
        int idx = rand.nextInt(numBenes);
        Account bene = beneList.get(idx);
        sendTransaction(step, amount, hub, bene, isFraud, (int)alertID);  // Main account makes transactions to one of the neighbors
        List<Account> nbs = bene.getDests();
        int numNbs = nbs.size();
        if(numNbs > 0){
//            idx = (int)(step % numNbs);  // Choose one of its neighbors
            idx = rand.nextInt(numNbs);
            Account nb = nbs.get(idx);
            sendTransaction(step, amount, bene, nb, isFraud, (int)alertID);  // Neighbor accounts make transactions
        }
    }
}
