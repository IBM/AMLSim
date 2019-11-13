package amlsim;

import amlsim.model.aml.*;
import sim.engine.SimState;

import java.util.Map;

/**
 * Suspicious account class
 */
public class SARAccount extends Account {

	private int count = 0;

	SARAccount(String id, int modelID, int interval, float init_balance, int start, int end, String bankID, Map<String, String> attrs){
		super(id, modelID, interval, init_balance, start, end, bankID, attrs);
	}


	public void handleAction(SimState state){
		AMLSim amlsim = (AMLSim) state;
		long step = state.schedule.getSteps();

		for(Alert ag : alerts){
            if(this == ag.getPrimaryAccount()){
                ag.registerTransactions(step, this);
            }
		}

		this.model.sendTransaction(step);
		boolean success = handleAlert(amlsim);
		if(success){
			count++;
		}
	}

	private boolean handleAlert(AMLSim amlsim){
		if(alerts.isEmpty()){
			return false;
		}

		Alert fg = alerts.get(count % alerts.size());
		AMLTypology model = fg.getModel();

		model.sendTransaction(amlsim.schedule.getSteps());
		return true;
	}

	public String toString() {
		return "F" + this.id;
	}

}
