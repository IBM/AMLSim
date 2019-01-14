package amlsim;

import amlsim.model.fraud.*;
import sim.engine.SimState;

/**
 * Suspicious account class
 */
public class FraudAccount extends Account {

	private int count = 0;

	FraudAccount(long id, int modelID, float init_balance, int start, int end){
		super(id, modelID, init_balance, start, end);
	}


	public void handleAction(SimState state){
		AMLSim amlsim = (AMLSim) state;

		for(Alert ag : groups){
			ag.registerTransactions(state.schedule.getSteps());
		}

		boolean success = handleTransaction(amlsim);
		if(!success) {
			success = handleFraud(amlsim);
		}
		if(success){
			count++;
		}
	}

	private boolean handleFraud(AMLSim amlsim){
		if(groups.isEmpty()){
			return false;
		}

		Alert fg = groups.get(count % groups.size());
		FraudTransactionModel model = fg.getModel();

		model.sendTransaction(amlsim.schedule.getSteps());
//		List<AMLTransaction> txs = model.sendTransaction(amlsim.schedule.getSteps());
//		if(txs == null || txs.isEmpty()){
//			return false;
//		}
//
//		for(AMLTransaction tx : txs) {
//			double amount = tx.getAmount();
//			Account dstAfter = tx.getClientDestAfter();
//			Account dstBefore = new Account();
//			dstBefore.setAccount(dstAfter);
//
//			Account srcBefore = new Account();
//			srcBefore.setAccount(this);
//			this.withdraw(amount);
//			dstAfter.deposit(amount);
//
//			tx.setDay(this.getCurrDay());
//			tx.setHour(this.getCurrHour());
//			tx.setClientDestAfter(dstAfter);
//			tx.setClientDestBefore(dstBefore);
//			tx.setFraud(true);
//			amlsim.getTrans().add(tx);
//		}
		return true;
	}

	public String getName() {
		return Long.toString(this.id);
	}

	public String toString() {
		return "F" + Integer.toString(this.hashCode());
	}

}
