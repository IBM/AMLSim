package amlsim.model.normal;

import amlsim.Account;
import amlsim.model.AbstractTransactionModel;

import java.util.List;

/**
 * Send money from single source to multiple destinations (fan-out)
 * Note: This model is used by SAR accounts
 */
public class SuspiciousFanOutTransactionModel extends AbstractTransactionModel {


    public void setParameters(int interval, float balance, long start, long end){
        super.setParameters(interval, balance, start, end);
        if(this.startStep < 0){  // decentralize the first transaction step
            this.startStep = generateStartStep(interval);
        }
    }

    @Override
    public String getType() {
        return "SARFanOut";
    }

    @Override
    public void sendTransaction(long step) {
        if((step - startStep) % interval != 0){
            return;
        }
        List<Account> beneList = this.account.getBeneList();
//        int numBene = beneList.size();
//        int index = (int)(step - startStep) % interval;
//        if(index < 0){
//            index += interval;
//        }
//        if(index >= numBene || numBene == 0){  // No more destination accounts
//            return;
//        }

        for(Account dest : beneList) {
//                    Account dest = beneList.get(index);
            float amount = getSuspiciousTransactionAmount();
            this.sendTransaction(step, amount, dest);
        }
    }
}
