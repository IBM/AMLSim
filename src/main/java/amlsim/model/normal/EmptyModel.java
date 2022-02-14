package amlsim.model.normal;

import java.util.Random;

import amlsim.Account;
import amlsim.AccountGroup;
import amlsim.model.AbstractTransactionModel;

/**
 * Empty transaction model (It does not make any transactions)
 * Used when invalid model IDs are specified
 */
public class EmptyModel extends AbstractTransactionModel {

    public EmptyModel(
        AccountGroup accountGroup,
        Random random
    ) {
    }

    @Override
    public String getModelName() {
        return "Default";
    }

    @Override
    public void sendTransactions(long step, Account origAccount) {
        // Do nothing in default
    }
}
