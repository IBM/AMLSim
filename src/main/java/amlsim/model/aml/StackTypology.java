//
// Note: No specific bank models are used for this AML typology model class.
//

package amlsim.model.aml;

import amlsim.Account;

/**
 * Stacked bipartite transactions
 */
public class StackTypology extends AMLTypology {
    
    @Override
    public void setParameters(int modelID) {
    }

//    @Override
//    public int getNumTransactions() {
//        int total_members = alert.getMembers().size();
//        int orig_members = total_members / 3;  // First 1/3 accounts are originator accounts
//        int mid_members = orig_members;  // Second 1/3 accounts are intermediate accounts
//        int bene_members = total_members - orig_members * 2;  // Rest of accounts are beneficiary accounts
//        return orig_members * mid_members + mid_members + bene_members;
//    }

    StackTypology(double minAmount, double maxAmount, int minStep, int maxStep) {
        super(minAmount, maxAmount, minStep, maxStep);
    }

    @Override
    public String getModelName() {
        return "StackTypology";
    }

    @Override
    public void sendTransactions(long step, Account acct) {

        int total_members = alert.getMembers().size();
        int orig_members = total_members / 3;  // First 1/3 accounts are originator accounts
        int mid_members = orig_members;  // Second 1/3 accounts are intermediate accounts
        int bene_members = total_members - orig_members * 2;  // Rest of accounts are beneficiary accounts

        double amount1 = getRandomAmount();
        double total_flow = amount1 * orig_members * mid_members;  // Total transaction amount
        double amount2 = total_flow / (mid_members * bene_members);

        for(int i=0; i<orig_members; i++){  // originator accounts --> Intermediate accounts
            Account orig = alert.getMembers().get(i);
            if(!orig.getID().equals(acct.getID())){
                continue;
            }

            for(int j=orig_members; j<(orig_members+mid_members); j++){
                Account bene = alert.getMembers().get(j);
                makeTransaction(step, amount1, orig, bene);
            }
        }

        for(int i=orig_members; i<(orig_members+mid_members); i++){   // Intermediate accounts --> Beneficiary accounts
            Account orig = alert.getMembers().get(i);
            if(!orig.getID().equals(acct.getID())){
                continue;
            }

            for(int j=(orig_members+mid_members); j<total_members; j++){
                Account bene = alert.getMembers().get(j);
                makeTransaction(step, amount2, orig, bene);
            }
        }
    }
}
