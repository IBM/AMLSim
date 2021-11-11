//
// Note: No specific bank models are used for this AML typology model class.
//

package amlsim.model.aml;

import amlsim.AMLSim;
import amlsim.Account;
import amlsim.TargetedTransactionAmount;

import java.util.*;

/**
 * The main account makes a transaction with one of the neighbor accounts
 * and the neighbor also makes transactions with its neighbors.
 * The beneficiary account and amount of each transaction are determined randomly.
 */
public class RandomTypology extends AMLTypology {

    private static Random random = AMLSim.getRandom();
    private Set<Long> steps = new HashSet<>();  // Set of simulation steps when the transaction is performed
    private Account nextOrig;  // Originator account for the next transaction

    @Override
    public void setParameters(int modelID) {
        int numMembers = alert.getMembers().size();
        for(int i=0; i<numMembers; i++) {
            steps.add(getRandomStep());
        }
        nextOrig = alert.getMainAccount();
    }

//    @Override
//    public int getNumTransactions() {
//        return alert.getMembers().size();
//    }

    RandomTypology(double minAmount, double maxAmount, int minStep, int maxStep) {
        super(minAmount, maxAmount, minStep, maxStep);
    }

    @Override
    public String getModelName() {
        return "RandomTypology";
    }

    public boolean isValidStep(long step){
        return super.isValidStep(step) && steps.contains(step);
    }

    public void sendTransactions(long step, Account acct){
        boolean isSAR = alert.isSAR();
        long alertID = alert.getAlertID();
        if(!isValidStep(step))return;

        List<Account> beneList = nextOrig.getBeneList();
        int numBenes = beneList.size();
        if(numBenes == 0)return;

        int idx = random.nextInt(numBenes);
        Account bene = beneList.get(idx);

        TargetedTransactionAmount transactionAmount = new TargetedTransactionAmount(nextOrig.getBalance(), random);
        makeTransaction(step, transactionAmount.doubleValue(), nextOrig, bene, isSAR, (int)alertID);  // Main account makes transactions to one of the neighbors
        nextOrig = bene;  // The next originator account is the previous beneficiary account
    }
}
