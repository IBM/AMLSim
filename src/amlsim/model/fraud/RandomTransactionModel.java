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

    public RandomTransactionModel(float minAmount, float maxAmount, int minStep, int maxStep) {
        super(minAmount, maxAmount, minStep, maxStep);
    }

    @Override
    public String getType() {
        return "DenseFraud";
    }


//    private double getDoublePrecision(double d) {
//        final int precision = 2;
//        return (new BigDecimal(d)).setScale(precision, BigDecimal.ROUND_HALF_UP).doubleValue();
//    }

//    public synchronized void writeLog(Collection<AMLTransaction> txs) {
//        try {
//            FileWriter writer1 = new FileWriter(new File(AMLSim.logFileName), true);
//            BufferedWriter writer = new BufferedWriter(writer1);
//            for(AMLTransaction tx : txs) {
//                writer.write(tx.getStep() + "," + tx.getDescription() + ","
//                        + this.getDoublePrecision(tx.getAmount()) + "," + tx.getClientOrigBefore().getName() + ","
//                        + this.getDoublePrecision(tx.getClientOrigBefore().getBalance()) + ","
//                        + this.getDoublePrecision(tx.getClientOrigAfter().getBalance()) + ","
//                        + tx.getClientDestAfter().getName() + ","
//                        + this.getDoublePrecision(tx.getClientDestBefore().getBalance()) + ","
//                        + this.getDoublePrecision(tx.getClientDestAfter().getBalance()) + ","
//                        + (tx.isFraud() ? 1 : 0) + "," + tx.getAlertID() + "\n");
//                writer.flush();
//            }
//            writer.close();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//    }

//    private void flushLog(Collection<AMLTransaction> txs){
//        writeLog(txs);
//        txs.clear();
//    }

    public void sendTransactions(long step){
//        final int THREADS = 8;

//        if(AMLSim.TX_OPT){
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
//        }else {
//            final int BUFFER = 1000;
//            ConcurrentLinkedQueue<AMLTransaction> txs = new ConcurrentLinkedQueue<>();
//            if (!isValidStep(step)) return;
//
//            Account hub = this.alert.getMembers().get(0);
//            List<Account> dests = hub.getDests();
//            float amount = getAmount() / dests.size();
//
//            int numDests = dests.size();
//            int stepRange = this.endStep - this.startStep + 1;
//            int eachMembers = 1;
//            int start = ((int) step - this.startStep) * eachMembers;
//            int end = min(numDests - 1, ((int) step - this.startStep + 1) * eachMembers);
//
//            ExecutorService service = Executors.newFixedThreadPool(THREADS);
//
//            for (int i = start; i < end; i++) {
//                final int idx = i;
//
//                service.submit(() -> {
//                    Account dest = dests.get(idx);
//                    sendTransaction(step, amount, hub, dest);
//
//                    // Send neighbors
//                    List<Account> nbs = dest.getDests();
//                    for (Account nb : nbs) {
//                        sendTransaction(step, amount, dest, nb);
//                        if (txs.size() >= BUFFER) {
//                            flushLog(txs);
//                            assert txs.isEmpty();
//                        }
//                    }
//                    if (txs.size() >= BUFFER) {
//                        flushLog(txs);
//                        assert txs.isEmpty();
//                    }
//                });
//            }
//
//            service.shutdown();
//        }
    }

//    @Override
//    public Collection<AMLTransaction> sendTransactions(long step) {
//        final int BUFFER = 1000;
//
//        ArrayList<AMLTransaction> txs = new ArrayList<>();
//        boolean isFraud = alert.isFraud();
//        long alertID = alert.getAlertID();
//
//        if(!isValidStep(step))return txs;
//
//        AMLClient hub = this.alert.getMembers().get(0);
//        List<AMLClient> dests = hub.getDests();
//        float amount = getAmount() / dests.size();
//
//        int numDests = dests.size();
//        int stepRange = this.endStep - this.startStep + 1;
//        int eachMembers = max(1, numDests/stepRange);
//        int start = ((int)step - this.startStep) * eachMembers;
//        int end = min(numDests-1, ((int)step - this.startStep + 1) * eachMembers);
//
//        for(int i=start; i<end; i++){
//            AMLClient dest = dests.get(i);
//            AMLTransaction tx = sendTransaction(step, amount, hub, dest);
//            tx.setAlertID(alertID);
//            tx.setFraud(isFraud);
//            txs.add(tx);
//
//            // Send neighbors
//            List<AMLClient> nbs = dest.getDests();
//            for(AMLClient nb : nbs){
//                AMLTransaction tx1 = sendTransaction(step, amount, dest, nb);
//                tx1.setAlertID(alertID);
//                tx1.setFraud(isFraud);
//                txs.add(tx1);
//                if(txs.size() >= BUFFER){
//                    flushLog(txs);
//                    assert txs.isEmpty();
//                }
//            }
//            if(txs.size() >= BUFFER){
//                flushLog(txs);
//                assert txs.isEmpty();
//            }
//        }
//        return txs;
//    }
}
