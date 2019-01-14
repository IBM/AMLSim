package amlsim.model.cash;

import amlsim.AMLSim;
import amlsim.obsolete.AMLTransaction;
import amlsim.Branch;

import static java.lang.Math.round;

/**
 * Cash-out (withdrawal) model
 */
public class CashOutModel extends CashModel {

    private static int NORMAL_INTERVAL = 1;
    private static int CASE_INTERVAL = 1;
    private static float NORMAL_MIN = 10;
    private static float NORMAL_MAX = 100;
    private static float CASE_MIN = 10;
    private static float CASE_MAX = 100;

    public static void setParam(int norm_int, int case_int, float norm_min, float norm_max, float case_min, float case_max){
        NORMAL_INTERVAL = norm_int;
        CASE_INTERVAL = case_int;
        NORMAL_MIN = norm_min;
        NORMAL_MAX = norm_max;
        CASE_MIN = case_min;
        CASE_MAX = case_max;
    }

    private boolean isNextStep(long step){
        double g = randValues[(int)step % rsize];
        double g1 = (g + 1.0) / 2;  // from 0.0 to 1.0

        if(this.account.isCase()){
            long dt = round(CASE_INTERVAL * g1);
            return step % CASE_INTERVAL == dt;
        }else {
            long dt = round(NORMAL_INTERVAL * g1);
            return step % NORMAL_INTERVAL == dt;
        }
    }

    private float computeAmount(){
        if(this.account.isCase()){
            return CASE_MIN + rand.nextFloat() * (CASE_MAX - CASE_MIN);
        }else{
            return NORMAL_MIN + rand.nextFloat() * (NORMAL_MAX - NORMAL_MIN);
        }
    }

    @Override
    public String getType() {
        return "CASH-OUT";
    }

    @Override
    public void sendTransaction(long step) {
//        List<AMLTransaction> txs = new ArrayList<>();
        if(isNextStep(step)){
            if(AMLSim.TX_OPT){  // Do not create AMLTransaction objects
                Branch branch = account.getBranch();
                float amount = computeAmount();
                sendTransaction(step, amount, branch, account, "CASH-OUT");
            }else {
                Branch branch = account.getBranch();
                float amount = computeAmount();
                AMLTransaction tx = new AMLTransaction(step, account, (short) 0, amount, "CASH-OUT");
                tx.setClientDestAfter(branch);
                account.withdraw(amount);
//                txs.add(tx);
            }
        }
//        return txs;
    }

//    @Override
//    public void sent() {
//
//    }
}
