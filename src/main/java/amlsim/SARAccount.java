package amlsim;

import java.util.Random;

import amlsim.model.aml.*;
import sim.engine.SimState;

/**
 * Suspicious account class
 */
public class SARAccount extends Account {

	private int count = 0;

	SARAccount(String id, int interval, float init_balance, String bankID, Random random) {
		super(id, interval, init_balance, bankID, random);
		this.isSAR = true;
	}

	public void handleAction(SimState state){
	    AMLSim amlsim = (AMLSim) state;
		super.handleAction(amlsim);

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

		// this is no-op
		// figure out why this was here.
		model.makeTransaction(amlsim.schedule.getSteps());
		return true;
	}

	public String toString() {
		return "F" + this.id;
	}

}
