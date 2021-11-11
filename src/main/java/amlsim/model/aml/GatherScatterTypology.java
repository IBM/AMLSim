package amlsim.model.aml;

import amlsim.AMLSim;
import amlsim.Account;
import amlsim.TargetedTransactionAmount;

import java.util.*;

/**
 * Gather-Scatter transaction model (Multiple accounts -> fan-in -> main account -> fan-out -> multiple accounts)
 */
public class GatherScatterTypology extends AMLTypology {

    private List<Account> origAccts = new ArrayList<>();
    private List<Account> beneAccts = new ArrayList<>();
    private long[] gatherSteps;
    private long[] scatterSteps;
    private long middleStep;
    private double totalReceivedAmount = 0.0;
    private double scatterAmount = 0.0;  // Scatter transaction amount will be defined after gather transactions
    private Random random = AMLSim.getRandom();

    GatherScatterTypology(double minAmount, double maxAmount, int startStep, int endStep) {
        super(minAmount, maxAmount, startStep, endStep);
    }

    @Override
    public void setParameters(int modelID) {
        middleStep = (startStep + endStep) / 2;
//        System.out.println(startStep + " " + middleStep + " " + endStep);

        int numSubMembers = alert.getMembers().size() - 1;
        int numOrigMembers = numSubMembers / 2;
        int numBeneMembers = numSubMembers - numOrigMembers;

        gatherSteps = new long[numOrigMembers];
        scatterSteps = new long[numBeneMembers];

        Account mainAcct = alert.getMainAccount();
        List<Account> subMembers = new ArrayList<>();
        for (Account acct : alert.getMembers()){
            if(acct != mainAcct){
                subMembers.add(acct);
            }
        }
        assert(numSubMembers == subMembers.size());
        for(int i=0; i<numSubMembers; i++){
            Account acct = subMembers.get(i);
            if(i < numOrigMembers){
                origAccts.add(acct);
            }else{
                beneAccts.add(acct);
            }
        }

        // Ensure the specified period
        gatherSteps[0] = startStep;
        for(int i=1; i<numOrigMembers; i++){
            gatherSteps[i] = getRandomStepRange(startStep, middleStep);
        }
        scatterSteps[0] = endStep;
        for(int i=1; i<numBeneMembers; i++){
            scatterSteps[i] = getRandomStepRange(middleStep + 1, endStep);
        }
    }

//    @Override
//    public int getNumTransactions() {
//        return origAccts.size() + beneAccts.size();
//    }

    @Override
    public void sendTransactions(long step, Account acct) {
        long alertID = alert.getAlertID();
        boolean isSAR = alert.isSAR();
        int numGathers = gatherSteps.length;
        int numScatters = scatterSteps.length;

        if(step <= middleStep){
            for(int i=0; i<numGathers; i++){
                if(gatherSteps[i] == step){
                    Account orig = origAccts.get(i);
                    Account bene = alert.getMainAccount();
                    double amount = new TargetedTransactionAmount(orig.getBalance(), random).doubleValue();
                    makeTransaction(step, amount, orig, bene, isSAR, alertID);
                    totalReceivedAmount += amount;
                }
            }
        }else{
            for(int i=0; i<numScatters; i++){
                if(scatterSteps[i] == step){
                    Account orig = alert.getMainAccount();
                    Account bene = beneAccts.get(i);
                    double target = Math.min(orig.getBalance(), scatterAmount);
                    TargetedTransactionAmount transactionAmount = new TargetedTransactionAmount(target, random);
                    makeTransaction(step, transactionAmount.doubleValue(), orig, bene, isSAR, alertID);
                }
            }
        }
        if(step == middleStep){  // Define the amount of scatter transactions
            double margin = totalReceivedAmount * marginRatio;
            scatterAmount = (totalReceivedAmount - margin) / numScatters;
        }
    }

    @Override
    public String getModelName() {
        return "GatherScatterTypology";
    }
}

