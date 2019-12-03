package amlsim;

import amlsim.model.AbstractTransactionModel;
import amlsim.model.aml.*;
import amlsim.model.normal.SuspiciousFanOutTransactionModel;
import sim.engine.SimState;

import java.util.Map;

/**
 * Suspicious account class
 */
public class SARAccount extends Account {

	protected AbstractTransactionModel sarModel;  // SAR account make suspicious transactions as well as normal transactions
	private int count = 0;

	SARAccount(String id, int modelID, int interval, float init_balance, int start, int end, String bankID, Map<String, String> attrs){
		super(id, modelID, interval, init_balance, start, end, bankID, attrs);
		this.sarModel = new SuspiciousFanOutTransactionModel();
		this.sarModel.setAccount(this);
	}

	public void setSARModelParameters(int interval){
		this.sarModel.setParameters(interval, (float)this.getBalance(), this.startStep, this.endStep);
	}

	public void handleAction(SimState state){
	    AMLSim amlsim = (AMLSim) state;
		super.handleAction(amlsim);

		long step = state.schedule.getSteps();
		sarModel.sendTransaction(step);

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
