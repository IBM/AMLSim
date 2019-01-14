package amlsim.model.normal;

import amlsim.model.AbstractTransactionModel;

/**
 * Empty transaction model which does nothing
 * Used when invalid model IDs are specified
 */
public class EmptyModel extends AbstractTransactionModel {
    @Override
    public String getType() {
        return "Default";
    }

    @Override
    public void sendTransaction(long step) {
        // Do nothing in default
    }
}
