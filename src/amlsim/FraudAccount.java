package amlsim;

import amlsim.model.fraud.*;
import sim.engine.SimState;

import java.util.Map;

/**
 * Suspicious account class
 */
public class FraudAccount extends Account {

	private int count = 0;

    FraudAccount(String id, int modelID, int interval, float init_balance, int start, int end, Map<String, String> attrs){
		super(id, modelID, interval, init_balance, start, end, attrs);
	}


	public void handleAction(SimState state){
		AMLSim amlsim = (AMLSim) state;
		long step = state.schedule.getSteps();

		for(Alert ag : alerts){
            if(this == ag.getMainAccount()){
                ag.registerTransactions(step, this);
            }
		}

		this.model.sendTransaction(step);
		boolean success = handleFraud(amlsim);
		if(success){
			count++;
		}
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

	public String toString() {
		return "F" + this.id;
	}

}
