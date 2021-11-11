package amlsim;

import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;

import java.util.Random;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.when;

public class TargetedTransactionAmountTests {
    public Random random;

    @BeforeEach
    void beforeEach()
    {
        this.random = new Random(1);

    }

    @Test
    void testTargetIsMin()
    {
        SimProperties mockedSimProperties = mock(SimProperties.class);
        when(mockedSimProperties.getMinTransactionAmount()).thenReturn(100.0);
        when(mockedSimProperties.getMaxTransactionAmount()).thenReturn(200.0);

        try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class)) {
            mocked.when(AMLSim::getSimProp).thenReturn(mockedSimProperties);
            TargetedTransactionAmount transactionAmount = new TargetedTransactionAmount(100.0, this.random);
            assertEquals(100.0, transactionAmount.doubleValue());
        }
    }


    @Test
    void testTargetIsMid()
    {
        SimProperties mockedSimProperties = mock(SimProperties.class);
        when(mockedSimProperties.getMinTransactionAmount()).thenReturn(100.0);
        when(mockedSimProperties.getMaxTransactionAmount()).thenReturn(200.0);

        try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class)) {
            mocked.when(AMLSim::getSimProp).thenReturn(mockedSimProperties);
            TargetedTransactionAmount transactionAmount = new TargetedTransactionAmount(150.0, this.random);
            assertEquals(150.0, transactionAmount.doubleValue());
        }
    }


    @Test
    void testTargetIsMidWideRange()
    {
        SimProperties mockedSimProperties = mock(SimProperties.class);
        when(mockedSimProperties.getMinTransactionAmount()).thenReturn(100.0);
        when(mockedSimProperties.getMaxTransactionAmount()).thenReturn(4000.0);

        try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class)) {
            mocked.when(AMLSim::getSimProp).thenReturn(mockedSimProperties);
            TargetedTransactionAmount transactionAmount = new TargetedTransactionAmount(300.0, this.random);
            assertTrue(transactionAmount.doubleValue() <= 300.0);
            assertTrue(transactionAmount.doubleValue() >= 100.0);
        }
    }


    @Test
    void testTargetIsBelowMin()
    {
        SimProperties mockedSimProperties = mock(SimProperties.class);
        when(mockedSimProperties.getMinTransactionAmount()).thenReturn(100.0);
        when(mockedSimProperties.getMaxTransactionAmount()).thenReturn(4000.0);

        try (MockedStatic<AMLSim> mocked = mockStatic(AMLSim.class)) {
            mocked.when(AMLSim::getSimProp).thenReturn(mockedSimProperties);
            TargetedTransactionAmount transactionAmount = new TargetedTransactionAmount(40.0, this.random);
            assertEquals(40.0, transactionAmount.doubleValue());
        }
    }
}
