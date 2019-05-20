package com.ibm.amlsim;

import com.ibm.amlsim.model.fraud.*;
import sim.engine.SimState;

import java.util.Map;

/**
 * Suspicious account class
 */
public class FraudAccount extends Account {

	private int count = 0;

//	FraudAccount(long id, int modelID, float init_balance, int start, int end){
    FraudAccount(String id, int modelID, float init_balance, int start, int end, Map<String, String> attrs){
		super(id, modelID, init_balance, start, end, attrs);
	}


	public void handleAction(SimState state){
		AMLSim amlsim = (AMLSim) state;
		long step = state.schedule.getSteps();

		for(Alert ag : alerts){
			ag.registerTransactions(state.schedule.getSteps());
		}

		this.model.sendTransaction(step);
		boolean success = handleFraud(amlsim);
		if(success){
			count++;
		}
//		boolean success = handleTransaction(amlsim);
//		if(!success) {
//			success = handleFraud(amlsim);
//		}
//		if(success){
//			count++;
//		}
	}

	private boolean handleFraud(AMLSim amlsim){
		if(alerts.isEmpty()){
			return false;
		}

		Alert fg = alerts.get(count % alerts.size());
		FraudTransactionModel model = fg.getModel();

		model.sendTransaction(amlsim.schedule.getSteps());
		return true;
	}

//	public String getName() {
//		return Long.toString(this.id);
//	}

	public String toString() {
		return "F" + this.id;
	}

}
