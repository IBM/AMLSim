package amlsim;

import amlsim.model.aml.*;
import sim.engine.SimState;

/**
 * Suspicious account class
 */
public class SARAccount extends Account {

	private int count = 0;

	SARAccount(String id, int modelID, int interval, float init_balance, int start, int end, String bankID){
		super(id, modelID, interval, init_balance, start, end, bankID);
		this.isSAR = true;
	}

//	public void setSARModelParameters(int interval){
//		this.sarModel.setParameters(interval, (float)this.getBalance(), this.startStep, this.endStep);
//	}

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

		model.sendTransaction(amlsim.schedule.getSteps());
		return true;
	}

	public String toString() {
		return "F" + this.id;
	}

}
