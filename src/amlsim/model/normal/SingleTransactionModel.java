package amlsim.model.normal;

import amlsim.AMLSim;
import amlsim.Account;
import amlsim.model.AbstractTransactionModel;

import java.util.List;
import java.util.Random;

/**
 * Send money only once to one of neighbor accounts
 */
public class SingleTransactionModel extends AbstractTransactionModel {

    private int index = 0;
    private static Random rand = new Random();
//    private long[] steps;
    private long targetStep = 0;

    public String getType(){
        return "Single";
    }

    public void setParameters(float balance, long start, long end){
        super.setParameters(balance, start, end);
    }

    public void sendTransaction(long step){
        List<Account> dests = this.account.getDests();
        int numDests = dests.size();

//        if(step < this.startStep || this.endStep < step || dests.isEmpty()){
//            return;
//        }
        if(numDests == 0)return;
//        if(step == this.startStep){
//            steps = rand.longs(numDests, this.startStep, this.endStep + 1).sorted().toArray();
//        }
        if(step == 0){
            targetStep = rand.nextLong() % (AMLSim.getNumOfSteps() - 1) + 1;  // 1 --> NUM_OF_STEPS
        }

//        if(index >= numDests)return;  // This account has already sent to all neighbors

        float amount = this.balance;
//        long stepRange = this.endStep - this.startStep + 1;
//        long stepRange = AMLSim.getNumOfSteps();
//        int numPerStep = numDests / (int)stepRange;
//
//        if(numPerStep == 0){
//            if(step == steps[index]) {
//                Account dest = dests.get(index);
//                this.sendTransaction(step, amount, dest);
//                index++;
//            }
//        }else{
//            int start = index;
//            int end = Math.min(index + numPerStep, numDests);
//            for(int i=start; i<end; i++){
//                Account dest = dests.get(i % numDests);
//                this.sendTransaction(step, amount, dest);
//            }
//            index += numPerStep;
//        }
        if(step == targetStep){
            index = rand.nextInt() % numDests;
            Account dest = dests.get(index);
            this.sendTransaction(step, amount, dest);
        }
    }
}
