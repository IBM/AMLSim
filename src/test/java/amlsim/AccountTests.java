package amlsim;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;

import amlsim.AMLSim;
import amlsim.Account;
import amlsim.model.ModelParameters;
import sim.engine.Schedule;
import amlsim.SimProperties;

import java.util.Random;

import org.mockito.MockedStatic;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.when;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.times;



class AccountTests {
    public Schedule schedule;
    public AMLSim amlSim;

    @BeforeEach
    void beforeEach()
    {
        this.schedule = mock(Schedule.class);
        this.amlSim = mock(AMLSim.class);
        this.amlSim.schedule = this.schedule;
    }

    @Test
    void zeroSteps()
    {
        long step = 0;
        when(this.schedule.getSteps()).thenReturn(step);

        try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class)) {
            mocked.when(AMLSim::getRandom).thenReturn(new Random(1));

            Account anAccount = new Account("1", 0, 5, 1000.0f, 0, 1);
            anAccount.handleAction(amlSim);

            mocked.verify(() -> AMLSim.handleTransaction(1, "TRANSFER", 1000.0f, anAccount, anAccount, false, 1), never());
        }
    }

    @Test
    void SingleTransactionModelBenefitListZero()
    {
        long step = 1;
        when(this.schedule.getSteps()).thenReturn(step);

        Account anAccount = new Account("1", 0, 5, 1000.0f, 1, 1);
        Account beneAccount = new Account("2", 0, 5, 1000.0f, 1, 1);

        try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class)) 
        {
            mocked.when(AMLSim::getRandom).thenReturn(new Random(1));

            
            anAccount.handleAction(amlSim);

            mocked.verify(() -> AMLSim.handleTransaction(1L, "TRANSFER", 3.0f, anAccount, beneAccount, false, -1L), never());
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
            when(mockedProperties.getNormalBaseTxAmount()).thenReturn(3.00f);

            mocked.when(AMLSim::getRandom).thenReturn(new Random(1));
            mocked.when(AMLSim::getSimProp).thenReturn(
                mockedProperties
            );
            mockey.when(() -> ModelParameters.shouldAddEdge(any(), any())).thenReturn(true);

            Account anAccount = new Account("1", 0, 5, 1000.0f, 1, 1);
            Account beneAccount = new Account("2", 0, 5, 1000.0f, 1, 1);
            
            anAccount.addBeneAcct(beneAccount);
            anAccount.addTxType(beneAccount, "TRANSFER");
            
            anAccount.handleAction(amlSim);
            mocked.verify(() -> AMLSim.handleTransaction(1L, "TRANSFER", 3.0f, anAccount, beneAccount, false, -1L), times(1));
        }
    }
}
