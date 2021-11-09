package amlsim.model.normal;

import java.util.Random;

import amlsim.Account;
import amlsim.model.AbstractTransactionModel;

/**
 * Empty transaction model (It does not make any transactions)
 * Used when invalid model IDs are specified
 */
public class EmptyModel extends AbstractTransactionModel {

    public EmptyModel(
        Account account,
        Random random
    ) {
    }

    @Override
    public String getModelName() {
        return "Default";
    }

    @Override
    public void makeTransaction(long step) {
        // Do nothing in default
    }
}
