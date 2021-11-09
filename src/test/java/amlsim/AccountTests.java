package amlsim;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;

import amlsim.model.AbstractTransactionModel;
import amlsim.model.ModelParameters;
import sim.engine.Schedule;

import java.util.Random;
import java.util.logging.Logger;

import org.mockito.MockedStatic;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.when;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.times;


// How to mock static
// try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class)) {
    // mocked.when(AMLSim::getRandom).thenReturn(new Random(1));


class AccountTests {
    public Schedule schedule;
    public AMLSim amlSim;
    public SimProperties simProperties;
    public Random random;

    @BeforeEach
    void beforeEach()
    {
        this.schedule = mock(Schedule.class);
        this.amlSim = mock(AMLSim.class);
        this.amlSim.schedule = this.schedule;
        this.simProperties = mock(SimProperties.class);
        this.random = new Random(1);
    }

    @Test
    void zeroSteps()
    {
        long step = 0;
        when(this.schedule.getSteps()).thenReturn(step);

        try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class)) {
            mocked.when(AMLSim::getRandom).thenReturn(new Random(1));

            Account anAccount = new Account("1", AbstractTransactionModel.SINGLE, 5, 1000.0f, 0, 1, "bankid", this.random);
            anAccount.handleAction(amlSim);

            mocked.verify(() -> AMLSim.handleTransaction(1, "TRANSFER", 1000.0f, anAccount, anAccount, false, 1), never());
        }
    }

    @Test
    void SingleTransactionModelBenefitListZero()
    {
        long step = 1;
        when(this.schedule.getSteps()).thenReturn(step);

        Account anAccount = new Account("1", AbstractTransactionModel.SINGLE, 5, 1000.0f, 1, 1, "bankid", this.random);
        Account beneAccount = new Account("2", AbstractTransactionModel.SINGLE, 5, 1000.0f, 1, 1, "bankid", this.random);

        try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class)) 
        {
            mocked.when(AMLSim::getRandom).thenReturn(new Random(1));
            anAccount.handleAction(amlSim);

            mocked.verify(() -> AMLSim.handleTransaction(1L, "TRANSFER", 3.0, anAccount, beneAccount, false, -1L), never());
        }
    }


    @Test
    public void SingleTransactionModelBenefitListExists()
    {
        long step = 1;
        when(this.schedule.getSteps()).thenReturn(step);

        try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class);
            MockedStatic<ModelParameters> mockey = mockStatic(ModelParameters.class)
        ) 
        {
            SimProperties mockedProperties = mock(SimProperties.class);
            when(mockedProperties.getMaxTransactionAmount()).thenReturn(100.0);

            mocked.when(AMLSim::getRandom).thenReturn(new Random(1));
            mocked.when(AMLSim::getSimProp).thenReturn(
                mockedProperties
            );
            mocked.when(AMLSim::getLogger).thenReturn(
                Logger.getLogger("AMLSim")
            );
            mockey.when(() -> ModelParameters.shouldAddEdge(any(), any())).thenReturn(true);

            Account anAccount = new Account("1", AbstractTransactionModel.SINGLE, 5, 1000.0f, 1, 1, "bankid", this.random);
            Account beneAccount = new Account("2", AbstractTransactionModel.SINGLE, 5, 1000.0f, 1, 1, "bankid", this.random);
            
            anAccount.addBeneAcct(beneAccount);
            anAccount.addTxType(beneAccount, "TRANSFER");
            
            anAccount.handleAction(amlSim);
            mocked.verify(() -> AMLSim.handleTransaction(1L, "TRANSFER", 40.74398012118764d, anAccount, beneAccount, false, -1L), times(1));
        }
    }
}
